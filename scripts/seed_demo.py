"""Synthetic demonstration data; runs only when inventory is empty."""
import sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database import connect
from rules import today_jakarta
today=today_jakarta()
tools=[
('LAB-001','Proyektor praktikum','Presentasi','Rak A / Lab 1','Baik','Remote dan kabel HDMI lengkap'),
('LAB-002','Multimeter digital','Elektronika','Rak B / Lab 1','Baik dengan catatan','Baterai cadangan tersedia'),
('LAB-003','Router jaringan','Jaringan','Rak C / Lab 2','Baik','Adaptor 12 V lengkap'),
('LAB-004','Kamera dokumentasi','Multimedia','Lemari A / Lab 2','Dalam perawatan','Pemeriksaan lensa'),
('LAB-005','Tripod kamera','Multimedia','Lemari B / Lab 2','Baik','Tas penyimpanan lengkap')]
with connect(write=True) as conn:
    if conn.execute('SELECT COUNT(*) AS n FROM equipment').fetchone()['n']:
        print('Inventaris sudah berisi data; seed tidak mengubahnya.')
        sys.exit(0)
    ids=[]
    for tool in tools:
        cursor=conn.execute('INSERT INTO equipment(code,name,category,location,condition,notes) VALUES (?,?,?,?,?,?)',tool)
        ids.append(cursor.lastrowid)
        conn.execute("INSERT INTO audit_log(action,entity,entity_id,detail) VALUES ('Tambah','alat',?,'Data DEMO sintetis')",(cursor.lastrowid,))
    rows=[
(ids[0],'Demo Mahasiswa A','DEMO-A','Presentasi praktikum',0,3,'Baik',None,None),
(ids[1],'Demo Mahasiswa B','DEMO-B','Pengukuran rangkaian',-4,-1,'Baik dengan catatan',None,None),
(ids[2],'Demo Mahasiswa C','DEMO-C','Konfigurasi LAN',-5,-2,'Baik',-1,'Baik')]
    for tool,borrower,nim,purpose,start,end,condition,returned,return_condition in rows:
        cursor=conn.execute("""INSERT INTO loans(equipment_id,borrower,nim,purpose,borrowed_on,due_on,
            checkout_condition,checkout_notes,returned_on,return_condition,return_notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",(tool,borrower,nim,purpose,
            (today+timedelta(days=start)).isoformat(),(today+timedelta(days=end)).isoformat(),condition,
            'Data DEMO; kelengkapan diperiksa',
            (today+timedelta(days=returned)).isoformat() if returned is not None else None,
            return_condition,'Lengkap' if returned is not None else ''))
        conn.execute("INSERT INTO audit_log(action,entity,entity_id,detail) VALUES ('Tambah','peminjaman',?,'Transaksi DEMO sintetis')",(cursor.lastrowid,))
print('Seed selesai: 5 alat, 3 transaksi. Semua nama/NIM merupakan data DEMO.')
