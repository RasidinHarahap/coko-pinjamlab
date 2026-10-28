import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rules import equipment_values, loan_values


class BusinessRulesTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 6)
        self.loan = dict(equipment_id="1", borrower="Sinta", nim="26001", purpose="Praktikum",
                         borrowed_on="2026-10-05", due_on="2026-10-07")

    def test_equipment_normalizes_code_and_trim(self):
        value = equipment_values(dict(code=" lab-01 ", name=" Proyektor ", category=" Presentasi ", location="Rak A", condition="Baik"))
        self.assertEqual(value["code"], "LAB-01")
        self.assertEqual(value["name"], "Proyektor")

    def test_required_name(self):
        with self.assertRaisesRegex(ValueError, "Nama alat wajib"):
            equipment_values(dict(code="L01", name=" ", category="Lab", location="Rak A", condition="Baik"))

    def test_field_limit(self):
        with self.assertRaisesRegex(ValueError, "maksimal 40"):
            equipment_values(dict(code="X" * 41, name="Alat", category="Lab", location="Rak A", condition="Baik"))

    def test_valid_loan(self):
        value = loan_values(self.loan, self.today)
        self.assertEqual(value["equipment_id"], 1)
        self.assertEqual(value["borrowed_on"], date(2026, 10, 5))

    def test_due_before_borrowed(self):
        with self.assertRaisesRegex(ValueError, "sebelum"):
            loan_values(dict(self.loan, due_on="2026-10-04"), self.today)

    def test_future_borrowed(self):
        with self.assertRaisesRegex(ValueError, "hari ini"):
            loan_values(dict(self.loan, borrowed_on="2026-10-07"), self.today)

    def test_invalid_date(self):
        with self.assertRaisesRegex(ValueError, "Tanggal"):
            loan_values(dict(self.loan, due_on="2026-02-30"), self.today)

    def test_invalid_equipment(self):
        with self.assertRaisesRegex(ValueError, "Pilih alat"):
            loan_values(dict(self.loan, equipment_id="abc"), self.today)


if __name__ == "__main__":
    unittest.main(verbosity=2)
