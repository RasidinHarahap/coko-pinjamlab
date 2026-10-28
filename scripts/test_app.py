"""Integration tests against real, isolated SQLite databases (no DB mocks)."""
import csv
import io
import json
import os
import re
import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SECRET_KEY', 'integration-test-key-isolated-only-' * 2)
from app import app
from database import connect
from init_db import initialize
from rules import today_jakarta

app.config['TESTING'] = True


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = os.environ.get('DB_PATH')
        os.environ['DB_PATH'] = str(Path(self.temp.name) / 'test.sqlite3')
        initialize()
        self.client = app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as s:
            self.token = s['csrf_token']
        self.tool = dict(code='LAB-T001', name='Alat Uji', category='Presentasi',
                         location='Rak A', condition='Baik', notes='Data uji sintetis')
        self.loan = dict(equipment_id='1', borrower='Peminjam Uji', nim='DEMO-001',
                         purpose='Praktikum', borrowed_on=today_jakarta().isoformat(),
                         due_on=(today_jakarta()+timedelta(days=3)).isoformat(),
                         checkout_notes='Kabel lengkap')

    def tearDown(self):
        if self.old_path is None:
            os.environ.pop('DB_PATH', None)
        else:
            os.environ['DB_PATH'] = self.old_path
        self.temp.cleanup()

    def post(self, path, data=None, follow=False):
        return self.client.post(path, data={'csrf_token':self.token, **(data or {})},
                                follow_redirects=follow)

    def create_tool(self, **changes):
        response = self.post('/alat/baru', {**self.tool, **changes})
        self.assertEqual(response.status_code, 302)
        return response

    def create_loan(self, **changes):
        self.create_tool()
        response = self.post('/peminjaman/baru', {**self.loan, **changes})
        self.assertEqual(response.status_code, 302)
        return response

    def scalar(self, sql, params=()):
        with connect() as conn:
            return next(iter(conn.execute(sql, params).fetchone().values()))

    def test_empty_pages_and_health(self):
        for path in ('/','/alat','/peminjaman','/alat/baru','/peminjaman/baru','/aktivitas'):
            self.assertEqual(self.client.get(path).status_code,200,path)
        self.assertEqual(self.client.get('/health').json['status'],'ok')
        self.assertEqual(self.client.get('/health').json['version'],'5.0')

    def test_equipment_create_read_update_delete(self):
        self.create_tool()
        self.assertIn(b'Alat Uji',self.client.get('/alat').data)
        self.assertEqual(self.post('/alat/1/ubah',{**self.tool,'name':'Alat Diperbarui'}).status_code,302)
        self.assertEqual(self.scalar('SELECT name FROM equipment'),'Alat Diperbarui')
        self.assertEqual(self.post('/alat/1/hapus').status_code,302)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM equipment'),0)

    def test_duplicate_equipment_code(self):
        self.create_tool()
        self.assertEqual(self.post('/alat/baru',self.tool).status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM equipment'),1)

    def test_required_fields_and_limits(self):
        for changes in ({'name':''},{'location':''},{'notes':'x'*501},{'code':'x'*41}):
            self.assertEqual(self.post('/alat/baru',{**self.tool,**changes}).status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM equipment'),0)

    def test_invalid_equipment_condition(self):
        self.assertEqual(self.post('/alat/baru',{**self.tool,'condition':'Tidak sah'}).status_code,400)

    def test_equipment_search(self):
        self.create_tool()
        self.assertIn(b'Alat Uji',self.client.get('/alat?q=Rak+A').data)
        self.assertNotIn(b'<strong>Alat Uji</strong>',self.client.get('/alat?q=TidakAda').data)
        self.assertIn(b'<strong>Alat Uji</strong>',self.client.get('/alat?availability=Tersedia').data)
        self.assertNotIn(b'<strong>Alat Uji</strong>',self.client.get('/alat?availability=Dipinjam').data)
        self.post('/alat/baru',{**self.tool,'code':'LAB-T002','name':'Alat Rusak','condition':'Rusak'})
        self.assertIn(b'<strong>Alat Rusak</strong>',self.client.get('/alat?availability=Perlu+perhatian').data)
        self.assertNotIn(b'<strong>Alat Uji</strong>',self.client.get('/alat?q=Alat+Uji&availability=Perlu+perhatian').data)
        self.assertIn(b'<strong>Alat Uji</strong>',self.client.get('/alat?q=Alat+Uji&availability=Tersedia').data)

    def test_loan_create_read_update_delete(self):
        self.create_loan()
        self.assertEqual(self.scalar('SELECT checkout_condition FROM loans'),'Baik')
        self.assertIn(b'Peminjam Uji',self.client.get('/peminjaman').data)
        self.assertEqual(self.post('/peminjaman/1/ubah',{**self.loan,'purpose':'Praktikum lanjutan'}).status_code,302)
        self.assertEqual(self.scalar('SELECT purpose FROM loans'),'Praktikum lanjutan')
        self.post('/peminjaman/1/hapus')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM loans'),0)

    def test_double_active_loan_is_rejected(self):
        self.create_loan()
        self.assertEqual(self.post('/peminjaman/baru',self.loan).status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM loans'),1)

    def test_concurrent_loans_have_one_winner(self):
        self.create_tool()
        def submit(index):
            with app.test_client() as client:
                client.get('/')
                with client.session_transaction() as s:
                    token = s['csrf_token']
                return client.post('/peminjaman/baru',data={**self.loan,
                    'borrower':f'Peminjam Uji {index}','csrf_token':token}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = sorted(pool.map(submit,(1,2)))
        self.assertEqual(statuses,[302,400])
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM loans'),1)

    def test_damaged_or_maintenance_tools_unavailable(self):
        for condition in ('Rusak','Dalam perawatan'):
            with connect(write=True) as conn:
                conn.execute('DELETE FROM equipment')
            self.create_tool(condition=condition)
            tool_id = self.scalar('SELECT id FROM equipment')
            self.assertEqual(self.post('/peminjaman/baru',{**self.loan,'equipment_id':tool_id}).status_code,400)
            self.assertNotIn(b'LAB-T001',self.client.get('/peminjaman/baru').data)

    def test_future_borrow_date_rejected(self):
        self.create_tool()
        future = (today_jakarta()+timedelta(days=1)).isoformat()
        self.assertEqual(self.post('/peminjaman/baru',{**self.loan,'borrowed_on':future}).status_code,400)

    def test_reverse_or_invalid_dates_rejected(self):
        self.create_tool()
        for changes in ({'due_on':(today_jakarta()-timedelta(days=1)).isoformat()},
                        {'borrowed_on':'2026-02-30'},{'due_on':'invalid'}):
            self.assertEqual(self.post('/peminjaman/baru',{**self.loan,**changes}).status_code,400)

    def test_seven_day_limit_and_boundary(self):
        self.create_tool()
        self.assertEqual(self.post('/peminjaman/baru',{**self.loan,
            'due_on':(today_jakarta()+timedelta(days=8)).isoformat()}).status_code,400)
        self.assertEqual(self.post('/peminjaman/baru',{**self.loan,
            'due_on':(today_jakarta()+timedelta(days=7)).isoformat()}).status_code,302)

    def test_missing_equipment_rejected(self):
        self.assertEqual(self.post('/peminjaman/baru',{**self.loan,'equipment_id':'999'}).status_code,400)

    def test_historical_equipment_cannot_be_changed(self):
        self.create_loan()
        self.create_tool(code='LAB-T002')
        self.assertEqual(self.post('/peminjaman/1/ubah',{**self.loan,'equipment_id':'2'}).status_code,400)
        self.assertEqual(self.scalar('SELECT equipment_id FROM loans'),1)

    def test_foreign_key_prevents_equipment_deletion(self):
        self.create_loan()
        self.post('/alat/1/hapus')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM equipment'),1)
        with self.assertRaises(sqlite3.IntegrityError):
            with connect(write=True) as conn:
                conn.execute('DELETE FROM equipment WHERE id=1')

    def test_return_updates_inventory_condition(self):
        self.create_loan()
        self.assertEqual(self.post('/peminjaman/1/kembalikan',
            {'return_condition':'Dalam perawatan','return_notes':'Kabel perlu diganti'}).status_code,302)
        self.assertEqual(self.scalar('SELECT condition FROM equipment'),'Dalam perawatan')
        self.assertEqual(self.scalar('SELECT return_condition FROM loans'),'Dalam perawatan')
        self.assertEqual(self.post('/peminjaman/baru',self.loan).status_code,400)

    def test_return_with_notes_required(self):
        self.create_loan()
        self.assertEqual(self.post('/peminjaman/1/kembalikan',
            {'return_condition':'Rusak','return_notes':''}).status_code,400)
        self.assertIsNone(self.scalar('SELECT returned_on FROM loans'))

    def test_return_is_idempotent_and_tool_reborrowable(self):
        self.create_loan()
        data={'return_condition':'Baik','return_notes':''}
        self.post('/peminjaman/1/kembalikan',data)
        self.post('/peminjaman/1/kembalikan',data)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM audit_log WHERE action='Kembali'"),1)
        self.assertEqual(self.post('/peminjaman/baru',self.loan).status_code,302)

    def test_active_condition_changed_only_at_return(self):
        self.create_loan()
        self.assertEqual(self.post('/alat/1/ubah',{**self.tool,'condition':'Rusak'}).status_code,400)
        self.assertEqual(self.scalar('SELECT condition FROM equipment'),'Baik')

    def test_late_status_and_filters(self):
        self.create_loan(borrowed_on=(today_jakarta()-timedelta(days=3)).isoformat(),
                         due_on=(today_jakarta()-timedelta(days=1)).isoformat())
        self.assertIn(b'Terlambat',self.client.get('/peminjaman?status=Terlambat').data)
        self.assertNotIn(b'Peminjam Uji',self.client.get('/peminjaman?status=Dipinjam').data)
        self.assertIn(b'Peminjam Uji',self.client.get('/peminjaman?q=DEMO-001').data)

    def test_csrf_and_safe_http_methods(self):
        self.assertEqual(self.client.post('/alat/baru',data=self.tool).status_code,400)
        self.assertEqual(self.client.get('/alat/1/hapus').status_code,405)
        self.assertEqual(self.client.post('/alat/baru',data={**self.tool,'csrf_token':'错误'}).status_code,400)

    def test_html_escaping_and_parameterized_query(self):
        self.create_tool(name='<script>alert(1)</script>')
        page=self.client.get('/alat').data
        self.assertIn(b'&lt;script&gt;',page)
        self.assertNotIn(b'<script>alert',page)
        self.assertEqual(self.client.get("/alat?q=%27%20OR%201%3D1--").status_code,200)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM equipment'),1)

    def test_receipt_and_csv_export_formula_safety(self):
        self.create_loan(borrower='=SUM(1,2)')
        receipt=self.client.get('/peminjaman/1/bukti')
        self.assertEqual(receipt.status_code,200)
        self.assertIn(b'PL-00001',receipt.data)
        self.assertIn(b'Kabel lengkap',receipt.data)
        export=self.client.get('/peminjaman/export.csv')
        rows=list(csv.DictReader(io.StringIO(export.data.decode('utf-8-sig'))))
        self.assertEqual(rows[0]['borrower'],"'=SUM(1,2)")
        self.assertEqual(rows[0]['checkout_condition'],'Baik')

    def test_audit_retained_after_delete(self):
        self.create_tool()
        self.post('/alat/1/hapus')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM audit_log'),2)
        self.assertIn(b'Hapus',self.client.get('/aktivitas').data)

    def test_persistence_reinitialize_and_integrity(self):
        self.create_tool()
        initialize()
        self.assertEqual(self.scalar('SELECT name FROM equipment'),'Alat Uji')
        self.assertEqual(self.scalar('PRAGMA integrity_check'),'ok')

    def test_missing_resource_and_security_headers(self):
        for path in ('/tidak-ada','/alat/999/ubah','/peminjaman/999/bukti','/peminjaman/999/kembalikan'):
            self.assertEqual(self.client.get(path).status_code,404)
        response=self.client.get('/')
        self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(response.headers['X-Frame-Options'],'SAMEORIGIN')
        self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
        self.assertIn("form-action 'self'", response.headers['Content-Security-Policy'])


if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ApplicationTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if '--json' in sys.argv:
        index=sys.argv.index('--json')
        destination=Path(sys.argv[index+1])
        destination.parent.mkdir(parents=True,exist_ok=True)
        from datetime import datetime, timezone
        import importlib.metadata
        destination.write_text(json.dumps(dict(
            tested_at=datetime.now(timezone.utc).isoformat(),
            scope=('Docker container + real SQLite' if os.environ.get('IN_CONTAINER') == '1' else 'Native Flask + real SQLite, not a Docker run'),
            python=sys.version.split()[0],flask=importlib.metadata.version('Flask'),
            sqlite=__import__('sqlite3').sqlite_version,
            tests=result.testsRun,passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
            failures=len(result.failures),errors=len(result.errors),
            cases=[test.id().split('.')[-1] for test,_ in result.failures+result.errors],
            successful=result.wasSuccessful()),indent=2),encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
