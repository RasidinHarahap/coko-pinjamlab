"""Seven isolated SQLite regression checks. Never modifies the operational database."""
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import connect
from init_db import initialize
from rules import today_jakarta


class SQLiteIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.previous = os.environ.get('DB_PATH')
        os.environ['DB_PATH'] = str(Path(self.directory.name) / 'isolated.sqlite3')
        initialize()
        with connect(write=True) as conn:
            conn.execute("INSERT INTO equipment(code,name,category,location,condition) "
                         "VALUES('SQL-001','Unit Uji','Uji','Rak A','Baik')")
        self.today = today_jakarta()

    def tearDown(self):
        if self.previous is None:
            os.environ.pop('DB_PATH', None)
        else:
            os.environ['DB_PATH'] = self.previous
        self.directory.cleanup()

    def add_loan(self, borrowed=None, due=None, returned=None):
        borrowed = borrowed or self.today
        due = due or (borrowed + timedelta(days=3))
        with connect(write=True) as conn:
            return conn.execute("INSERT INTO loans(equipment_id,borrower,nim,purpose,borrowed_on,due_on,"
                                "checkout_condition,returned_on,return_condition) VALUES "
                                "(1,'Uji','DEMO-SQL','Pengujian',?,?, 'Baik',?,?)",
                                (borrowed.isoformat(), due.isoformat(),
                                 returned.isoformat() if returned else None,
                                 'Baik' if returned else None)).lastrowid

    def test_repeated_initialize_does_not_delete_data(self):
        initialize()
        with connect() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM equipment').fetchone()['COUNT(*)'], 1)

    def test_duplicate_code_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with connect(write=True) as conn:
                conn.execute("INSERT INTO equipment(code,name,category,location) "
                             "VALUES('SQL-001','Duplikat','Uji','Rak B')")

    def test_second_active_loan_is_rejected(self):
        self.add_loan()
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_loan()

    def test_delete_referenced_equipment_is_rejected(self):
        self.add_loan()
        with self.assertRaises(sqlite3.IntegrityError):
            with connect(write=True) as conn:
                conn.execute('DELETE FROM equipment WHERE id=1')

    def test_over_seven_day_due_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_loan(due=self.today+timedelta(days=8))

    def test_transaction_rollback_restores_both_tables(self):
        loan_id=self.add_loan()
        with self.assertRaisesRegex(RuntimeError, 'rollback'):
            with connect(write=True) as conn:
                conn.execute('UPDATE loans SET returned_on=?,return_condition=? WHERE id=?',
                             (self.today.isoformat(),'Rusak',loan_id))
                conn.execute("UPDATE equipment SET condition='Rusak' WHERE id=1")
                raise RuntimeError('rollback')
        with connect() as conn:
            self.assertIsNone(conn.execute('SELECT returned_on FROM loans WHERE id=?',(loan_id,)).fetchone()['returned_on'])
            self.assertEqual(conn.execute('SELECT condition FROM equipment WHERE id=1').fetchone()['condition'],'Baik')

    def test_returned_unit_can_be_reborrowed_and_backed_up(self):
        first=self.add_loan()
        with connect(write=True) as conn:
            conn.execute('UPDATE loans SET returned_on=?,return_condition=? WHERE id=?',
                         (self.today.isoformat(),'Baik',first))
        self.add_loan()
        source=Path(os.environ['DB_PATH'])
        backup=Path(self.directory.name)/'backup.sqlite3'
        with sqlite3.connect(source) as src, sqlite3.connect(backup) as dst:
            src.backup(dst)
            self.assertEqual(dst.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(dst.execute('SELECT COUNT(*) FROM loans').fetchone()[0],2)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SQLiteIntegrityTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
