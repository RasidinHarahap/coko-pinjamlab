PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE CHECK(length(trim(code)) BETWEEN 1 AND 40),
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 120),
    category TEXT NOT NULL CHECK(length(trim(category)) BETWEEN 1 AND 80),
    location TEXT NOT NULL CHECK(length(trim(location)) BETWEEN 1 AND 80),
    condition TEXT NOT NULL DEFAULT 'Baik'
        CHECK(condition IN ('Baik','Baik dengan catatan','Dalam perawatan','Rusak')),
    notes TEXT NOT NULL DEFAULT '' CHECK(length(notes) <= 500),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE RESTRICT,
    borrower TEXT NOT NULL CHECK(length(trim(borrower)) BETWEEN 1 AND 120),
    nim TEXT NOT NULL CHECK(length(trim(nim)) BETWEEN 1 AND 40),
    purpose TEXT NOT NULL CHECK(length(trim(purpose)) BETWEEN 1 AND 240),
    borrowed_on TEXT NOT NULL CHECK(date(borrowed_on) IS NOT NULL),
    due_on TEXT NOT NULL CHECK(date(due_on) IS NOT NULL),
    returned_on TEXT CHECK(returned_on IS NULL OR date(returned_on) IS NOT NULL),
    checkout_condition TEXT NOT NULL CHECK(checkout_condition IN ('Baik','Baik dengan catatan')),
    checkout_notes TEXT NOT NULL DEFAULT '' CHECK(length(checkout_notes) <= 500),
    return_condition TEXT CHECK(return_condition IS NULL OR return_condition IN
        ('Baik','Baik dengan catatan','Dalam perawatan','Rusak')),
    return_notes TEXT NOT NULL DEFAULT '' CHECK(length(return_notes) <= 500),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    CHECK(due_on >= borrowed_on),
    CHECK(julianday(due_on)-julianday(borrowed_on) <= 7),
    CHECK(returned_on IS NULL OR returned_on >= borrowed_on),
    CHECK((returned_on IS NULL AND return_condition IS NULL) OR
          (returned_on IS NOT NULL AND return_condition IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_loan_per_equipment
ON loans(equipment_id) WHERE returned_on IS NULL;
CREATE INDEX IF NOT EXISTS loans_due_on ON loans(due_on);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity TEXT NOT NULL CHECK(entity IN ('alat','peminjaman')),
    entity_id INTEGER NOT NULL,
    detail TEXT NOT NULL,
    occurred_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
