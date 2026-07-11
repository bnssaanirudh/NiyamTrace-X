"""
data/synthetic/erp.py — Synthetic SQLite ERP for NiyamTrace sandbox.

Schema:
  vendor_invoices(invoice_id, vendor_id, month, year, amount_usd, status, created_at)

Seed: ~30 rows spanning vendors 4421, 8802, 3301 and months Jan–May 2025.

Design decisions:
- File-backed at data/synthetic/erp.db (not :memory:) so integration tests
  can inspect state before/after and replay bundles can snapshot it.
- A fresh seed is always re-applied by reset_to_seed() before each test run.
- "Deletion" in this system = status='TOMBSTONED' (retrieval-layer only).
  Records are never physically removed. See docs/decisions.md §3.

NEVER include real PII, employee, financial, or medical data here.
All vendor names, amounts, and IDs are synthetic.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
DEFAULT_DB_PATH = _HERE / "erp.db"

# ---------------------------------------------------------------------------
# Seed data — synthetic procurement invoices
# ---------------------------------------------------------------------------

_SEED_ROWS: list[dict] = [
    # Vendor 4421 — Jan through May 2025
    {"invoice_id": "INV-4421-2501", "vendor_id": 4421, "month": 1, "year": 2025, "amount_usd": 12400.00, "status": "OPEN",     "created_at": "2025-01-05"},
    {"invoice_id": "INV-4421-2502", "vendor_id": 4421, "month": 2, "year": 2025, "amount_usd": 9800.50,  "status": "OPEN",     "created_at": "2025-02-03"},
    {"invoice_id": "INV-4421-2503", "vendor_id": 4421, "month": 3, "year": 2025, "amount_usd": 15200.00, "status": "OPEN",     "created_at": "2025-03-07"},  # target
    {"invoice_id": "INV-4421-2504", "vendor_id": 4421, "month": 3, "year": 2025, "amount_usd": 8750.00,  "status": "OPEN",     "created_at": "2025-03-14"},  # target
    {"invoice_id": "INV-4421-2505", "vendor_id": 4421, "month": 3, "year": 2025, "amount_usd": 22100.75, "status": "OPEN",     "created_at": "2025-03-28"},  # target
    {"invoice_id": "INV-4421-2506", "vendor_id": 4421, "month": 4, "year": 2025, "amount_usd": 11300.00, "status": "OPEN",     "created_at": "2025-04-10"},
    {"invoice_id": "INV-4421-2507", "vendor_id": 4421, "month": 5, "year": 2025, "amount_usd": 5600.00,  "status": "OPEN",     "created_at": "2025-05-02"},
    # Vendor 8802 — Jan through May 2025
    {"invoice_id": "INV-8802-2501", "vendor_id": 8802, "month": 1, "year": 2025, "amount_usd": 7200.00,  "status": "OPEN",     "created_at": "2025-01-08"},
    {"invoice_id": "INV-8802-2502", "vendor_id": 8802, "month": 2, "year": 2025, "amount_usd": 13400.00, "status": "OPEN",     "created_at": "2025-02-12"},
    {"invoice_id": "INV-8802-2503", "vendor_id": 8802, "month": 3, "year": 2025, "amount_usd": 9900.00,  "status": "OPEN",     "created_at": "2025-03-11"},
    {"invoice_id": "INV-8802-2504", "vendor_id": 8802, "month": 4, "year": 2025, "amount_usd": 18600.00, "status": "OPEN",     "created_at": "2025-04-15"},
    {"invoice_id": "INV-8802-2505", "vendor_id": 8802, "month": 5, "year": 2025, "amount_usd": 4300.00,  "status": "CLOSED",   "created_at": "2025-05-20"},
    # Vendor 3301 — Jan through May 2025
    {"invoice_id": "INV-3301-2501", "vendor_id": 3301, "month": 1, "year": 2025, "amount_usd": 6100.00,  "status": "OPEN",     "created_at": "2025-01-15"},
    {"invoice_id": "INV-3301-2502", "vendor_id": 3301, "month": 2, "year": 2025, "amount_usd": 8200.00,  "status": "OPEN",     "created_at": "2025-02-18"},
    {"invoice_id": "INV-3301-2503", "vendor_id": 3301, "month": 3, "year": 2025, "amount_usd": 17500.00, "status": "OPEN",     "created_at": "2025-03-09"},
    {"invoice_id": "INV-3301-2504", "vendor_id": 3301, "month": 4, "year": 2025, "amount_usd": 21000.00, "status": "OPEN",     "created_at": "2025-04-22"},
    {"invoice_id": "INV-3301-2505", "vendor_id": 3301, "month": 5, "year": 2025, "amount_usd": 3800.00,  "status": "OPEN",     "created_at": "2025-05-30"},
    # Extra rows: already-closed / tombstoned to test gate checks
    {"invoice_id": "INV-4421-2401", "vendor_id": 4421, "month": 12, "year": 2024, "amount_usd": 19000.00, "status": "CLOSED",  "created_at": "2024-12-20"},
    {"invoice_id": "INV-8802-2401", "vendor_id": 8802, "month": 11, "year": 2024, "amount_usd": 11000.00, "status": "TOMBSTONED", "created_at": "2024-11-10"},
]

# Deterministic hash of seed state — used as data_snapshot_id in traces
SEED_SNAPSHOT_ID = hashlib.sha256(
    json.dumps(_SEED_ROWS, sort_keys=True).encode()
).hexdigest()[:16]


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they do not exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vendor_invoices (
            invoice_id   TEXT PRIMARY KEY,
            vendor_id    INTEGER NOT NULL,
            month        INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
            year         INTEGER NOT NULL,
            amount_usd   REAL    NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'OPEN',
            created_at   TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_vi_vendor
            ON vendor_invoices (vendor_id);
        CREATE INDEX IF NOT EXISTS idx_vi_period
            ON vendor_invoices (year, month);
    """)
    conn.commit()


def reset_to_seed(conn: sqlite3.Connection) -> None:
    """
    Wipe vendor_invoices and re-insert seed rows.
    Call this before every integration/replay test to guarantee a known state.
    """
    conn.execute("DELETE FROM vendor_invoices")
    conn.executemany(
        """INSERT INTO vendor_invoices
               (invoice_id, vendor_id, month, year, amount_usd, status, created_at)
           VALUES (:invoice_id, :vendor_id, :month, :year, :amount_usd, :status, :created_at)""",
        _SEED_ROWS,
    )
    conn.commit()


def seed_fresh(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Open (or create) the ERP database, create schema, seed data.
    Returns an open connection.
    """
    conn = get_connection(db_path)
    init_schema(conn)
    reset_to_seed(conn)
    return conn


# ---------------------------------------------------------------------------
# Read helpers — used by simulator and tests
# ---------------------------------------------------------------------------


def query_invoices(
    conn: sqlite3.Connection,
    *,
    vendor_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    status: str | None = None,
) -> list[dict]:
    """
    Return matching invoice rows as plain dicts.
    All filters are ANDed.  None means "no filter on this column."
    """
    clauses: list[str] = []
    params: list = []

    if vendor_id is not None:
        clauses.append("vendor_id = ?")
        params.append(vendor_id)
    if month is not None:
        clauses.append("month = ?")
        params.append(month)
    if year is not None:
        clauses.append("year = ?")
        params.append(year)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    cursor = conn.execute(
        f"SELECT * FROM vendor_invoices {where} ORDER BY invoice_id", params
    )
    return [dict(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Entry point — seed the on-disk DB when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB_PATH
    conn = seed_fresh(db_path)
    rows = query_invoices(conn)
    print(f"Seeded {len(rows)} rows into {db_path}")
    print(f"Seed snapshot ID: {SEED_SNAPSHOT_ID}")
    conn.close()
