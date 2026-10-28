"""Temporary persistence marker used by the container evidence collector."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database import connect
parser=argparse.ArgumentParser()
parser.add_argument('mode',choices=('create','verify','cleanup'))
parser.add_argument('code')
args=parser.parse_args()
with connect(write=True) as conn:
    if args.mode=='create':
        conn.execute("INSERT INTO equipment(code,name,category,location,condition) VALUES (?,'DEMO uji persistensi','Pengujian','Rak Uji','Baik')",(args.code,))
    elif args.mode=='verify':
        row=conn.execute('SELECT name FROM equipment WHERE code=?',(args.code,)).fetchone()
        if not row or row['name']!='DEMO uji persistensi':
            raise SystemExit('FAIL: marker database hilang setelah container dibuat ulang')
    else:
        conn.execute('DELETE FROM equipment WHERE code=?',(args.code,))
print(f'PASS: persistence {args.mode} · {args.code}')
