"""Seed a large dataset (10,000+ employees) for performance testing.

Usage:
    python seed_large.py --employees 10000 --reset
    python seed_large.py --employees 10000 --db ems_large.db

The script is deterministic (fixed random seed) so before/after measurements
are comparable. It never touches the default development database unless
--db points at it.
"""

import argparse
import os
import random
import sqlite3
from datetime import date, timedelta

from database import SCHEMA, apply_performance_indexes

FIRST_NAMES = [
    "Kwame", "Akosua", "Kojo", "Yaa", "Fiifi", "Adjoa", "Kwabena", "Esi",
    "Nii", "Abena", "Kofi", "Ama", "Efua", "Kwesi", "Akua", "Nana Ama",
    "Kojo", "Yaa", "Fiifi", "Esi", "Kwame", "Akosua", "Kofi", "Abena", "Kwesi",
    "Adjoa", "Nii", "Efua", "Akua", "Ama",
]
LAST_NAMES = [
    "Mensah", "Boateng", "Antwi", "Owusu", "Quartey", "Sarpong", "Osei",
    "Danso", "Armah", "Frimpong", "Asante", "Darko", "Appiah", "Badu", "Addo",
    "Nkrumah", "Tetteh", "Asamoah", "Annan", "Quansah", "Yeboah", "Ofori",
    "Frimpong", "Danso", "Osei", "Addo", "Badu", "Tetteh", "Quansah", "Annan",
]
JOB_TITLES = [
    "Software Engineer", "Senior Software Engineer", "Engineering Manager",
    "HR Officer", "Recruiter", "Accountant", "Financial Analyst", "Sales Executive",
    "Account Executive", "Marketing Specialist", "Content Strategist",
    "Graphic Designer", "Operations Analyst", "Customer Success Officer",
    "Data Analyst", "Product Manager", "QA Engineer", "Payroll Officer",
]
DEPARTMENTS = [
    ("Engineering", "Builds and maintains the company's software products."),
    ("Human Resources", "Recruiting, onboarding, payroll, and employee wellbeing."),
    ("Finance", "Budgeting, accounting, and financial reporting."),
    ("Sales", "Revenue generation and client relationships."),
    ("Marketing", "Brand, campaigns, and market research."),
]
STATUSES = ["active"] * 85 + ["on_leave"] * 10 + ["terminated"] * 5


def seed_large(conn: sqlite3.Connection, count: int) -> None:
    """Insert `count` employees into an existing schema."""
    rng = random.Random(42)
    today = date.today()

    if not conn.execute("SELECT COUNT(*) AS n FROM departments").fetchone()[0]:
        conn.executemany(
            "INSERT INTO departments (name, description) VALUES (?, ?)",
            DEPARTMENTS,
        )
    dept_ids = [
        row["id"]
        for row in conn.execute("SELECT id FROM departments ORDER BY id").fetchall()
    ]

    batch = []
    for i in range(1, count + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        dept_id = dept_ids[(i - 1) % len(dept_ids)]
        hire = date(2015, 1, 1) + timedelta(days=rng.randint(0, 4200))
        if hire > today:
            hire = today - timedelta(days=30)
        status = rng.choice(STATUSES)
        batch.append((
            f"EMP-{i:04d}",
            first,
            last,
            f"employee{i}@auspify.com",
            f"+233 24 555 {i:04d}",
            f"{rng.randint(1970, 2004)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            rng.choice(["Female", "Male"]),
            rng.choice(JOB_TITLES),
            dept_id,
            rng.randint(42000, 165000),
            hire.isoformat(),
            status,
            f"{rng.randint(1, 99)} Example Street, Accra",
        ))

    for start in range(0, len(batch), 500):
        chunk = batch[start:start + 500]
        conn.executemany(
            """
            INSERT INTO employees
                (employee_code, first_name, last_name, email, phone, date_of_birth,
                 gender, job_title, department_id, salary, hire_date, status, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            chunk,
        )
    conn.commit()

    # Make the first employee in each department its manager.
    for dept_id in dept_ids:
        row = conn.execute(
            "SELECT id FROM employees WHERE department_id = ? ORDER BY id LIMIT 1",
            (dept_id,),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE departments SET manager_id = ? WHERE id = ?",
                (row["id"], dept_id),
            )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Seed a large employee dataset.")
    parser.add_argument("--db", default="ems_large.db", help="SQLite database path")
    parser.add_argument("--employees", type=int, default=10000, help="Employee count")
    parser.add_argument("--reset", action="store_true", help="Delete the database first")
    parser.add_argument("--indexes", action="store_true", help="Add composite indexes")
    args = parser.parse_args()

    if args.reset and os.path.exists(args.db):
        os.remove(args.db)
        for suffix in ("-wal", "-shm"):
            path = args.db + suffix
            if os.path.exists(path):
                os.remove(path)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    existing = conn.execute("SELECT COUNT(*) AS n FROM employees").fetchone()[0]
    if existing:
        print(f"Database already has {existing} employees; leaving it unchanged.")
    else:
        seed_large(conn, args.employees)
        print(f"Seeded {args.employees} employees into {args.db}")
    if args.indexes:
        apply_performance_indexes(args.db)
        print("Composite performance indexes applied.")
    conn.close()


if __name__ == "__main__":
    main()
