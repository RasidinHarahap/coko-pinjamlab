"""PinjamLab: inventory, loans, condition handover, receipts, and audit trail."""
import csv
import io
import os
import secrets
import sqlite3
from datetime import timedelta

from flask import Flask, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for

from database import connect
from rules import BORROWABLE, CONDITIONS, MAX_LOAN_DAYS, equipment_values, loan_values, return_values, today_jakarta

app = Flask(__name__)
secret_key = os.environ.get("SECRET_KEY", "")
if len(secret_key) < 32 or secret_key.startswith("GANTI_"):
    raise RuntimeError("SECRET_KEY harus berupa kunci acak minimal 32 karakter. Jalankan scripts/setup-env.ps1.")
app.config.update(SECRET_KEY=secret_key, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  MAX_CONTENT_LENGTH=64 * 1024)


def audit(conn, action, entity, entity_id, detail):
    conn.execute("INSERT INTO audit_log(action,entity,entity_id,detail) VALUES (?,?,?,?)",
                 (action, entity, entity_id, detail))


def load_loan(conn, loan_id):
    row = conn.execute("""SELECT l.*,e.code,e.name AS equipment_name,e.location
        FROM loans l JOIN equipment e ON e.id=l.equipment_id WHERE l.id=?""", (loan_id,)).fetchone()
    if row is None:
        abort(404)
    row['status'] = ('Dikembalikan' if row['returned_on'] else
                     'Terlambat' if row['due_on'] < today_jakarta() else 'Dipinjam')
    return row


@app.before_request
def check_csrf():
    session.setdefault("csrf_token", secrets.token_hex(32))
    if request.method == "POST":
        submitted = request.form.get("csrf_token", "")
        if not secrets.compare_digest(submitted.encode(), session["csrf_token"].encode()):
            abort(400, description="Form kedaluwarsa atau token tidak valid. Muat ulang halaman.")


@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.context_processor
def page_context():
    return dict(csrf_token=session.get('csrf_token',''), today=today_jakarta(),
                conditions=CONDITIONS, max_loan_days=MAX_LOAN_DAYS)


@app.errorhandler(sqlite3.Error)
def database_error(error):
    app.logger.error('Database error: %s', type(error).__name__)
    return render_template('error.html', message='Database belum siap atau sedang sibuk. Periksa log aplikasi.'), 503


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
def http_error(error):
    message = 'Data atau halaman tidak ditemukan.' if error.code == 404 else error.description
    return render_template('error.html', message=message), error.code


@app.get('/health')
def health():
    with connect() as conn:
        conn.execute('SELECT COUNT(*) FROM equipment').fetchone()
        conn.execute('SELECT COUNT(*) FROM loans').fetchone()
    return jsonify(status='ok', database='SQLite connected', version='2.0')


@app.get('/')
def dashboard():
    with connect() as conn:
        stats = conn.execute("""SELECT (SELECT COUNT(*) FROM equipment) AS equipment,
            COUNT(*) FILTER (WHERE returned_on IS NULL) AS active,
            COUNT(*) FILTER (WHERE returned_on IS NULL AND due_on < ?) AS late,
            COUNT(*) FILTER (WHERE returned_on IS NOT NULL) AS returned FROM loans""",
            (today_jakarta().isoformat(),)).fetchone()
        recent = conn.execute("""SELECT l.*,e.name AS equipment_name,e.code,
            CASE WHEN l.returned_on IS NOT NULL THEN 'Dikembalikan'
                 WHEN l.due_on < ? THEN 'Terlambat' ELSE 'Dipinjam' END AS status
            FROM loans l JOIN equipment e ON e.id=l.equipment_id ORDER BY l.id DESC LIMIT 6""",
            (today_jakarta().isoformat(),)).fetchall()
    return render_template('dashboard.html', stats=stats, loans=recent)


@app.get('/alat')
def equipment_list():
    query = request.args.get('q','').strip()[:120]
    pattern = f'%{query}%'
    with connect() as conn:
        items = conn.execute("""SELECT e.*,EXISTS(SELECT 1 FROM loans l WHERE l.equipment_id=e.id
            AND l.returned_on IS NULL) AS is_borrowed FROM equipment e
            WHERE e.name LIKE ? OR e.code LIKE ? OR e.category LIKE ? OR e.location LIKE ?
            ORDER BY e.id DESC""", (pattern,)*4).fetchall()
    return render_template('equipment_list.html', items=items, query=query)


@app.route('/alat/baru', methods=['GET','POST'])
@app.route('/alat/<int:item_id>/ubah', methods=['GET','POST'])
def equipment_form(item_id=None):
    item, error = {}, None
    editing = item_id is not None
    if editing:
        with connect() as conn:
            item = conn.execute('SELECT * FROM equipment WHERE id=?',(item_id,)).fetchone()
        if item is None:
            abort(404)
    if request.method == 'POST':
        item = request.form
        try:
            values = equipment_values(request.form)
            fields = tuple(values[k] for k in ('code','name','category','location','condition','notes'))
            with connect(write=True) as conn:
                if item_id is None:
                    item_id = conn.execute("""INSERT INTO equipment(code,name,category,location,condition,notes)
                        VALUES (?,?,?,?,?,?)""",fields).lastrowid
                    action = 'Tambah'
                else:
                    old = conn.execute('SELECT * FROM equipment WHERE id=?',(item_id,)).fetchone()
                    if old is None:
                        abort(404)
                    active = conn.execute('SELECT id FROM loans WHERE equipment_id=? AND returned_on IS NULL',
                                          (item_id,)).fetchone()
                    if active and values['condition'] != old['condition']:
                        raise ValueError('Catat perubahan kondisi melalui pengembalian alat yang sedang dipinjam.')
                    conn.execute("""UPDATE equipment SET code=?,name=?,category=?,location=?,condition=?,notes=?
                        WHERE id=?""",fields+(item_id,))
                    action = 'Ubah'
                audit(conn,action,'alat',item_id,f"{values['code']} · {values['name']} · {values['condition']}")
            flash('Data alat berhasil disimpan.','success')
            return redirect(url_for('equipment_list'))
        except ValueError as exc:
            error = str(exc)
        except sqlite3.IntegrityError:
            error = 'Kode alat sudah digunakan atau data tidak valid. Pilih kode lain.'
    return render_template('equipment_form.html',item=item,editing=editing,error=error),400 if error else 200


@app.post('/alat/<int:item_id>/hapus')
def equipment_delete(item_id):
    try:
        with connect(write=True) as conn:
            row = conn.execute('SELECT * FROM equipment WHERE id=?',(item_id,)).fetchone()
            if row is None:
                abort(404)
            conn.execute('DELETE FROM equipment WHERE id=?',(item_id,))
            audit(conn,'Hapus','alat',item_id,f"{row['code']} · {row['name']}")
        flash('Data alat berhasil dihapus.','success')
    except sqlite3.IntegrityError:
        flash('Alat memiliki riwayat peminjaman. Hapus catatan peminjamannya terlebih dahulu jika diperlukan.','error')
    return redirect(url_for('equipment_list'))


def filtered_loans(conn):
    query = request.args.get('q','').strip()[:120]
    status = request.args.get('status','')
    if status not in ('','Dipinjam','Terlambat','Dikembalikan'):
        status = ''
    pattern = f'%{query}%'
    rows = conn.execute("""WITH entries AS (
        SELECT l.*,e.name AS equipment_name,e.code,
        CASE WHEN l.returned_on IS NOT NULL THEN 'Dikembalikan'
             WHEN l.due_on < ? THEN 'Terlambat' ELSE 'Dipinjam' END AS status
        FROM loans l JOIN equipment e ON e.id=l.equipment_id)
        SELECT * FROM entries WHERE (borrower LIKE ? OR nim LIKE ? OR equipment_name LIKE ? OR code LIKE ?)
        AND (?='' OR status=?) ORDER BY id DESC""",
        (today_jakarta().isoformat(),)+(pattern,)*4+(status,status)).fetchall()
    return rows,query,status


@app.get('/peminjaman')
def loan_list():
    with connect() as conn:
        rows,query,status = filtered_loans(conn)
    return render_template('loan_list.html',loans=rows,query=query,selected_status=status)


@app.route('/peminjaman/baru', methods=['GET','POST'])
@app.route('/peminjaman/<int:loan_id>/ubah', methods=['GET','POST'])
def loan_form(loan_id=None):
    item = dict(borrowed_on=today_jakarta(),due_on=today_jakarta()+timedelta(days=3))
    original, error = None, None
    if loan_id is not None:
        with connect() as conn:
            original = load_loan(conn,loan_id)
        item = original
    if request.method == 'POST':
        item = request.form
        try:
            values = loan_values(request.form)
            if original and values['equipment_id'] != original['equipment_id']:
                raise ValueError('Unit alat pada riwayat tidak dapat diganti. Buat transaksi baru untuk alat lain.')
            if original and original['returned_on'] and values['borrowed_on'] > original['returned_on']:
                raise ValueError('Tanggal pinjam tidak boleh setelah tanggal pengembalian.')
            with connect(write=True) as conn:
                tool = conn.execute('SELECT * FROM equipment WHERE id=?',(values['equipment_id'],)).fetchone()
                if not tool:
                    raise ValueError('Alat tidak ditemukan. Pilih alat yang tersedia.')
                fields = (values['borrower'],values['nim'],values['purpose'],values['borrowed_on'].isoformat(),
                          values['due_on'].isoformat(),values['checkout_notes'])
                if original is None:
                    if tool['condition'] not in BORROWABLE:
                        raise ValueError('Alat rusak atau dalam perawatan tidak dapat dipinjam.')
                    loan_id = conn.execute("""INSERT INTO loans(borrower,nim,purpose,borrowed_on,due_on,
                        checkout_notes,equipment_id,checkout_condition) VALUES (?,?,?,?,?,?,?,?)""",
                        fields+(tool['id'],tool['condition'])).lastrowid
                    action = 'Tambah'
                else:
                    conn.execute("""UPDATE loans SET borrower=?,nim=?,purpose=?,borrowed_on=?,due_on=?,
                        checkout_notes=? WHERE id=?""",fields+(loan_id,))
                    action = 'Ubah'
                audit(conn,action,'peminjaman',loan_id,f"{tool['code']} · {values['borrower']} · batas {values['due_on']}")
            flash('Data peminjaman berhasil disimpan.','success')
            return redirect(url_for('loan_receipt',loan_id=loan_id))
        except ValueError as exc:
            error = str(exc)
        except sqlite3.IntegrityError:
            error = 'Alat sedang dipinjam atau data transaksi tidak valid. Satu alat hanya memiliki satu peminjaman aktif.'
    with connect() as conn:
        equipment = conn.execute("""SELECT e.* FROM equipment e WHERE e.id=? OR
            (e.condition IN ('Baik','Baik dengan catatan') AND NOT EXISTS
            (SELECT 1 FROM loans l WHERE l.equipment_id=e.id AND l.returned_on IS NULL)) ORDER BY e.name""",
            (original['equipment_id'] if original else 0,)).fetchall()
    return render_template('loan_form.html',item=item,equipment=equipment,editing=original is not None,
                           original=original,error=error),400 if error else 200


@app.route('/peminjaman/<int:loan_id>/kembalikan',methods=['GET','POST'])
def loan_return(loan_id):
    error = None
    with connect() as conn:
        row = load_loan(conn,loan_id)
    if row['returned_on']:
        flash('Peminjaman ini sudah dikembalikan.','info')
        return redirect(url_for('loan_receipt',loan_id=loan_id))
    if request.method == 'POST':
        try:
            condition,notes = return_values(request.form)
            with connect(write=True) as conn:
                row = load_loan(conn,loan_id)
                if row['returned_on'] is None:
                    conn.execute('UPDATE loans SET returned_on=?,return_condition=?,return_notes=? WHERE id=?',
                                 (today_jakarta().isoformat(),condition,notes,loan_id))
                    conn.execute('UPDATE equipment SET condition=? WHERE id=?',(condition,row['equipment_id']))
                    audit(conn,'Kembali','peminjaman',loan_id,f"{row['code']} · kondisi {condition} · {notes}")
            flash('Pengembalian dan kondisi alat berhasil dicatat.','success')
            return redirect(url_for('loan_receipt',loan_id=loan_id))
        except ValueError as exc:
            error = str(exc)
    return render_template('return_form.html',loan=row,item=request.form,error=error),400 if error else 200


@app.get('/peminjaman/<int:loan_id>/bukti')
def loan_receipt(loan_id):
    with connect() as conn:
        row = load_loan(conn,loan_id)
    return render_template('receipt.html',loan=row)


@app.post('/peminjaman/<int:loan_id>/hapus')
def loan_delete(loan_id):
    with connect(write=True) as conn:
        row = load_loan(conn,loan_id)
        conn.execute('DELETE FROM loans WHERE id=?',(loan_id,))
        audit(conn,'Hapus','peminjaman',loan_id,f"{row['code']} · {row['borrower']}")
    flash('Catatan peminjaman berhasil dihapus. Jejak tindakan tetap tersimpan.','success')
    return redirect(url_for('loan_list'))


@app.get('/peminjaman/export.csv')
def loan_export():
    with connect() as conn:
        rows,_,_ = filtered_loans(conn)
    output = io.StringIO(newline='')
    output.write('\ufeff')
    writer = csv.writer(output)
    fields = ('id','code','equipment_name','borrower','nim','purpose','borrowed_on','due_on','returned_on',
              'status','checkout_condition','checkout_notes','return_condition','return_notes')
    writer.writerow(fields)
    for row in rows:
        values = []
        for key in fields:
            value = str(row[key]) if row[key] is not None else ''
            if value.lstrip().startswith(('=','+','-','@','\t','\r','\n')):
                value = "'"+value
            values.append(value)
        writer.writerow(values)
    return Response(output.getvalue(),mimetype='text/csv',headers={
        'Content-Disposition':'attachment; filename=pinjamlab-peminjaman.csv'})


@app.get('/aktivitas')
def activity_list():
    with connect() as conn:
        entries = conn.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT 100').fetchall()
    return render_template('activity.html',entries=entries)


if __name__ == '__main__':
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT','8080')),debug=False)
