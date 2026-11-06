"""
SQLite database helpers for Auspify EMS.

The schema is created automatically on first run. The application starts
with an empty database; there is no demo or seed data.

All connections enable foreign keys, as required by the project brief.
"""

import sqlite3
from flask import current_app, g

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
# NOTE: departments.manager_id and employees.department_id reference each
# other. SQLite allows this forward reference; it is resolved at insert time.
SCHEMA = """
CREATE TABLE IF NOT EXISTS departments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    description TEXT,
    manager_id  INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS employees (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code TEXT NOT NULL UNIQUE,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    phone         TEXT,
    date_of_birth TEXT,
    gender        TEXT,
    job_title     TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    salary        REAL NOT NULL DEFAULT 0 CHECK (salary >= 0),
    hire_date     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'on_leave', 'terminated')),
    address       TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Required indexes (employee_code/email also have implicit UNIQUE indexes).
CREATE INDEX IF NOT EXISTS idx_employees_employee_code ON employees(employee_code);
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_employees_last_name ON employees(last_name);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(status);
"""

def get_db() -> sqlite3.Connection:
    """Return one SQLite connection per Flask request."""
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DB_PATH"])
        db.row_factory = sqlite3.Row
        # Enforce foreign keys on every connection (SQLite default is OFF).
        db.execute("PRAGMA foreign_keys = ON")
        # WAL is a persistent database setting applied once in init_db();
        # repeating it on every connection would add avoidable overhead.
        db.execute("PRAGMA synchronous = NORMAL")
        g.db = db
    return g.db


def close_db(_exception=None):
    """Close the request-scoped connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(path: str, wal: bool = True) -> None:
    """Create the database schema at `path`. The app starts empty."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if wal:
        conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def apply_performance_indexes(path: str) -> None:
    """Composite indexes added after profiling (Step 5).

    These support the common filter combinations:
      - status + department (list and headcount)
      - department + status (department drill-down)
      - hire_date ranges (new hires)
    """
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_employees_status_department
            ON employees(status, department_id);
        CREATE INDEX IF NOT EXISTS idx_employees_department_status
            ON employees(department_id, status);
        CREATE INDEX IF NOT EXISTS idx_employees_hire_date
            ON employees(hire_date);
        """
    )
    conn.commit()
    conn.close()


def set_wal(path: str, enabled: bool) -> None:
    """Switch the database journal mode (used by the benchmark)."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode = " + ("WAL" if enabled else "DELETE"))
    conn.commit()
    conn.close()
