"""Online SQLite backup, including committed data from WAL."""
import argparse
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database import database_path
parser=argparse.ArgumentParser()
parser.add_argument('destination')
args=parser.parse_args()
destination=Path(args.destination)
source=database_path()
if not source.is_file():
    parser.error('Database sumber belum ada. Jalankan init_db.py terlebih dahulu.')
if source.resolve()==destination.resolve():
    parser.error('Tujuan backup harus berbeda dari database aktif.')
if destination.exists():
    parser.error('File tujuan sudah ada; pilih nama baru agar tidak tertimpa.')
destination.parent.mkdir(parents=True,exist_ok=True)
with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
    src.backup(dst)
    assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
print(f'Backup SQLite valid: {destination.name}')
