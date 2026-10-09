from datetime import date, datetime
from zoneinfo import ZoneInfo

CONDITIONS = ("Baik", "Baik dengan catatan", "Dalam perawatan", "Rusak")
BORROWABLE = CONDITIONS[:2]
MAX_LOAN_DAYS = 7


def today_jakarta():
    return datetime.now(ZoneInfo("Asia/Jakarta")).date()


def field(form, key, label, limit, required=True):
    value = str(form.get(key, "")).strip()
    if required and not value:
        raise ValueError(f"{label} wajib diisi.")
    if len(value) > limit:
        raise ValueError(f"{label} maksimal {limit} karakter.")
    return value


def equipment_values(form):
    code = field(form, "code", "Kode alat", 40).upper()
    if len(code) > 40:
        raise ValueError("Kode alat maksimal 40 karakter setelah dinormalisasi.")
    condition = field(form, "condition", "Kondisi", 40)
    if condition not in CONDITIONS:
        raise ValueError("Kondisi alat tidak valid.")
    return {
        "code": code,
        "name": field(form, "name", "Nama alat", 120),
        "category": field(form, "category", "Kategori", 80),
        "location": field(form, "location", "Lokasi penyimpanan", 80),
        "condition": condition,
        "notes": field(form, "notes", "Catatan", 500, required=False),
    }


def loan_values(form, today=None):
    current_day = today or today_jakarta()
    try:
        equipment_id = int(form.get("equipment_id", ""))
    except (ValueError, TypeError):
        raise ValueError("Pilih alat yang tersedia.") from None
    if equipment_id < 1:
        raise ValueError("Pilih alat yang tersedia.")
    values = {
        "equipment_id": equipment_id,
        "borrower": field(form, "borrower", "Nama peminjam", 120),
        "nim": field(form, "nim", "NIM", 40),
        "purpose": field(form, "purpose", "Keperluan", 240),
        "checkout_notes": field(form, "checkout_notes", "Catatan saat dipinjam", 500, required=False),
    }
    try:
        borrowed_on = date.fromisoformat(str(form.get("borrowed_on", "")))
        due_on = date.fromisoformat(str(form.get("due_on", "")))
    except (ValueError, TypeError):
        raise ValueError("Tanggal pinjam dan batas kembali harus valid.") from None
    if borrowed_on > current_day:
        raise ValueError("Tanggal pinjam tidak boleh melewati hari ini.")
    if due_on < borrowed_on:
        raise ValueError("Batas kembali tidak boleh sebelum tanggal pinjam.")
    if (due_on - borrowed_on).days > MAX_LOAN_DAYS:
        raise ValueError(f"Durasi peminjaman maksimal {MAX_LOAN_DAYS} hari.")
    values.update(borrowed_on=borrowed_on, due_on=due_on)
    return values


def return_values(form):
    condition = field(form, "return_condition", "Kondisi saat dikembalikan", 40)
    notes = field(form, "return_notes", "Catatan pengembalian", 500, required=False)
    if condition not in CONDITIONS:
        raise ValueError("Kondisi pengembalian tidak valid.")
    if condition != "Baik" and not notes:
        raise ValueError("Jelaskan catatan kondisi alat saat dikembalikan.")
    return condition, notes
