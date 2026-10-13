"""
data/seed.py — create and seed the ERP SQLite database.

Run once:  python data/seed.py

Creates data/erp.db with realistic procurement data:
  purchase_orders  — POs raised by the organisation
  vendors          — supplier master data
  materials        — product/material catalogue
  invoices         — billing from vendors
  goods_receipt    — confirmation of delivery
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "erp.db")


def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Schema ────────────────────────────────────────────────────────────

    c.executescript("""
    CREATE TABLE vendors (
        vendor_id      TEXT PRIMARY KEY,
        name           TEXT,
        country        TEXT,
        payment_terms  INTEGER,  -- days
        risk_rating    TEXT      -- Low / Medium / High
    );

    CREATE TABLE materials (
        material_id  TEXT PRIMARY KEY,
        name         TEXT,
        category     TEXT,
        unit_price   REAL,
        stock_level  INTEGER
    );

    CREATE TABLE purchase_orders (
        po_id        TEXT PRIMARY KEY,
        vendor_id    TEXT,
        material_id  TEXT,
        quantity     INTEGER,
        amount       REAL,
        date         TEXT,
        status       TEXT   -- Open / Closed / Cancelled
    );

    CREATE TABLE invoices (
        invoice_id  TEXT PRIMARY KEY,
        po_id       TEXT,
        amount      REAL,
        due_date    TEXT,
        paid_date   TEXT,   -- NULL if unpaid
        status      TEXT    -- Paid / Overdue / Pending
    );

    CREATE TABLE goods_receipt (
        gr_id             TEXT PRIMARY KEY,
        po_id             TEXT,
        quantity_received INTEGER,
        receipt_date      TEXT
    );
    """)

    # ── Vendors ───────────────────────────────────────────────────────────

    vendors = [
        ("V001", "Apex Components Ltd",     "Germany",    30, "Low"),
        ("V002", "Bright Supply Co",        "USA",        45, "Low"),
        ("V003", "CoreTech Industries",     "India",      30, "Medium"),
        ("V004", "Delta Logistics GmbH",    "Germany",    60, "Medium"),
        ("V005", "Eastern Parts Corp",      "China",      45, "High"),
        ("V006", "FastTrack Supplies",      "UK",         30, "Low"),
        ("V007", "Global Raw Materials",    "Brazil",     60, "High"),
        ("V008", "Horizon Electronics",     "Japan",      30, "Low"),
        ("V009", "Inland Packaging Ltd",    "USA",        30, "Medium"),
        ("V010", "JetStream Components",    "Germany",    45, "Low"),
    ]
    c.executemany("INSERT INTO vendors VALUES (?,?,?,?,?)", vendors)

    # ── Materials ─────────────────────────────────────────────────────────

    materials = [
        ("M001", "Steel Rods",          "Raw Material",  45.00, 500),
        ("M002", "Circuit Boards",      "Electronics",  120.00, 200),
        ("M003", "Packaging Boxes",     "Packaging",      3.50, 2000),
        ("M004", "Industrial Bolts",    "Fasteners",      0.80, 10000),
        ("M005", "Copper Wire",         "Raw Material",  22.00, 800),
        ("M006", "LCD Screens",         "Electronics",  180.00, 150),
        ("M007", "Plastic Pellets",     "Raw Material",   5.50, 3000),
        ("M008", "Hydraulic Pumps",     "Machinery",    350.00, 80),
        ("M009", "Safety Labels",       "Packaging",      0.20, 50000),
        ("M010", "Aluminium Sheets",    "Raw Material",  38.00, 600),
    ]
    c.executemany("INSERT INTO materials VALUES (?,?,?,?,?)", materials)

    # ── Purchase Orders ───────────────────────────────────────────────────

    random.seed(42)
    base_date = datetime(2024, 1, 1)
    pos = []
    for i in range(1, 51):
        po_id  = f"PO{i:03d}"
        vendor = random.choice(vendors)[0]
        mat    = random.choice(materials)
        qty    = random.randint(10, 500)
        amt    = round(qty * mat[3] * random.uniform(0.95, 1.05), 2)
        date   = (base_date + timedelta(days=random.randint(0, 270))).strftime("%Y-%m-%d")
        status = random.choice(["Open", "Open", "Closed", "Closed", "Closed", "Cancelled"])
        pos.append((po_id, vendor, mat[0], qty, amt, date, status))
    c.executemany("INSERT INTO purchase_orders VALUES (?,?,?,?,?,?,?)", pos)

    # ── Invoices ──────────────────────────────────────────────────────────

    invoices = []
    for i, po in enumerate(pos, 1):
        po_id, vendor_id = po[0], po[1]
        vendor_terms = next(v[3] for v in vendors if v[0] == vendor_id)
        po_date = datetime.strptime(po[5], "%Y-%m-%d")
        due = (po_date + timedelta(days=vendor_terms)).strftime("%Y-%m-%d")
        paid_date = None
        status = "Pending"
        if po[6] == "Closed":
            roll = random.random()
            if roll < 0.7:
                paid_date = (po_date + timedelta(days=vendor_terms - random.randint(0, 5))).strftime("%Y-%m-%d")
                status = "Paid"
            elif roll < 0.85:
                paid_date = (po_date + timedelta(days=vendor_terms + random.randint(1, 30))).strftime("%Y-%m-%d")
                status = "Paid"
            else:
                status = "Overdue"
        invoices.append((f"INV{i:03d}", po_id, po[4], due, paid_date, status))
    c.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?)", invoices)

    # ── Goods Receipts ────────────────────────────────────────────────────

    grs = []
    for i, po in enumerate(pos, 1):
        if po[6] in ("Closed", "Open"):
            po_date = datetime.strptime(po[5], "%Y-%m-%d")
            receipt = (po_date + timedelta(days=random.randint(3, 21))).strftime("%Y-%m-%d")
            qty_recv = po[3] if po[6] == "Closed" else random.randint(1, po[3])
            grs.append((f"GR{i:03d}", po[0], qty_recv, receipt))
    c.executemany("INSERT INTO goods_receipt VALUES (?,?,?,?)", grs)

    conn.commit()
    conn.close()
    print(f"✓ Database seeded: {DB_PATH}")
    print(f"  {len(vendors)} vendors, {len(materials)} materials, {len(pos)} POs, {len(invoices)} invoices, {len(grs)} goods receipts")


if __name__ == "__main__":
    seed()
