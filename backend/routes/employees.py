"""Employee endpoints: list/search/filter, detail, create, update, delete."""

import math
import sqlite3

from flask import Blueprint, jsonify, request

from database import get_db
from performance import invalidate_report_cache
from validation import STATUSES, is_valid_date, validate_employee

employees_bp = Blueprint("employees", __name__)

# Whitelist for the sort parameter. Never interpolate user input into SQL.
SORT_COLUMNS = {
    "first_name": "e.first_name",
    "last_name": "e.last_name",
    "email": "e.email",
    "employee_code": "e.employee_code",
    "hire_date": "e.hire_date",
    "salary": "e.salary",
    "status": "e.status",
    "department": "d.name",
    "created_at": "e.created_at",
}

EMPLOYEE_SELECT = """
    SELECT e.*, d.name AS department_name
    FROM employees e
    JOIN departments d ON d.id = e.department_id
"""

# The list screen only needs these columns; selecting them explicitly avoids
# transferring address/date-of-birth/gender for every row (Step 5).
EMPLOYEE_LIST_SELECT = """
    SELECT e.id, e.employee_code, e.first_name, e.last_name, e.email,
           e.job_title, e.department_id, e.salary, e.hire_date, e.status,
           d.name AS department_name
    FROM employees e
    JOIN departments d ON d.id = e.department_id
"""


def parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def escape_like(value):
    """Escape LIKE wildcards so a search for '%' is literal."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def employee_row(row):
    return dict(row) if row is not None else None


def fetch_employee(db, employee_id):
    return db.execute(
        EMPLOYEE_SELECT + "WHERE e.id = ?", (employee_id,)
    ).fetchone()


def next_employee_code(db):
    """Return the next EMP-#### code, skipping any gaps/duplicates."""
    rows = db.execute(
        "SELECT employee_code FROM employees WHERE employee_code LIKE 'EMP-%'"
    ).fetchall()
    highest = 0
    for row in rows:
        code = row["employee_code"]
        digits = code[4:]
        if digits.isdigit():
            highest = max(highest, int(digits))
    candidate = highest + 1
    while db.execute(
        "SELECT 1 FROM employees WHERE employee_code = ?", (f"EMP-{candidate:04d}",)
    ).fetchone():
        candidate += 1
    return f"EMP-{candidate:04d}"


def duplicate_email(db, email, exclude_id=None):
    sql = "SELECT 1 FROM employees WHERE LOWER(email) = LOWER(?)"
    params = [email]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    return db.execute(sql, params).fetchone() is not None


def duplicate_code(db, code, exclude_id=None):
    sql = "SELECT 1 FROM employees WHERE LOWER(employee_code) = LOWER(?)"
    params = [code]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    return db.execute(sql, params).fetchone() is not None


@employees_bp.get("/api/employees")
def list_employees():
    """List employees with search, filters, sorting, and pagination."""
    db = get_db()

    where = []
    params = []

    search = request.args.get("search", "").strip()
    if search:
        # One pass over a concatenated string is faster than four OR'ed LIKE
        # conditions and treats %/_ literally (no wildcard escaping needed).
        where.append(
            "instr(lower(e.first_name || ' ' || e.last_name || ' ' || e.email "
            "|| ' ' || e.employee_code), lower(?)) > 0"
        )
        params.append(search)

    department = request.args.get("department", "").strip()
    if department:
        if department.isdigit():
            where.append("e.department_id = ?")
            params.append(int(department))
        else:
            where.append("LOWER(d.name) = LOWER(?)")
            params.append(department)

    status = request.args.get("status", "").strip()
    if status:
        if status not in STATUSES:
            return jsonify(
                {"error": f"Status must be one of: {', '.join(STATUSES)}."}
            ), 400
        where.append("e.status = ?")
        params.append(status)
    elif not parse_bool(request.args.get("include_terminated")):
        # Soft-deleted employees are hidden by default.
        where.append("e.status != 'terminated'")

    job_title = request.args.get("job_title", "").strip()
    if job_title:
        where.append("e.job_title LIKE ? ESCAPE '\\'")
        params.append(f"%{escape_like(job_title)}%")

    hired_from = request.args.get("hired_from", "").strip()
    if hired_from:
        if not is_valid_date(hired_from):
            return jsonify({"error": "hired_from must use the YYYY-MM-DD format."}), 400
        where.append("e.hire_date >= ?")
        params.append(hired_from)

    hired_to = request.args.get("hired_to", "").strip()
    if hired_to:
        if not is_valid_date(hired_to):
            return jsonify({"error": "hired_to must use the YYYY-MM-DD format."}), 400
        where.append("e.hire_date <= ?")
        params.append(hired_to)

    sort = request.args.get("sort", "last_name")
    if sort not in SORT_COLUMNS:
        return jsonify(
            {"error": f"sort must be one of: {', '.join(sorted(SORT_COLUMNS))}."}
        ), 400
    order = request.args.get("order", "asc").lower()
    if order not in ("asc", "desc"):
        return jsonify({"error": "order must be asc or desc."}), 400

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 25))
    except (TypeError, ValueError):
        return jsonify({"error": "page and per_page must be integers."}), 400
    if page < 1 or per_page < 1:
        return jsonify({"error": "page and per_page must be positive."}), 400
    per_page = min(per_page, 100)

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    # The count query only needs the departments table when filtering by a
    # department name; otherwise a plain employees scan is enough.
    needs_department_join = bool(department and not department.isdigit())
    count_from = "FROM employees e"
    if needs_department_join:
        count_from += " JOIN departments d ON d.id = e.department_id"
    count = db.execute(
        "SELECT COUNT(*) AS total " + count_from + " " + where_sql,
        params,
    ).fetchone()["total"]

    total_pages = math.ceil(count / per_page) if count else 0
    offset = (page - 1) * per_page
    sort_column = SORT_COLUMNS[sort]
    rows = db.execute(
        EMPLOYEE_LIST_SELECT
        + where_sql
        + f" ORDER BY {sort_column} {order.upper()}, e.id ASC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()

    return jsonify(
        {
            "data": [employee_row(row) for row in rows],
            "meta": {
                "total": count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "returned": len(rows),
                "sort": sort,
                "order": order,
            },
        }
    )


@employees_bp.get("/api/employees/<int:employee_id>")
def get_employee(employee_id):
    db = get_db()
    row = fetch_employee(db, employee_id)
    if row is None:
        return jsonify({"error": "Employee not found."}), 404
    return jsonify({"data": employee_row(row)})


@employees_bp.post("/api/employees")
def create_employee():
    payload = request.get_json(silent=True)
    data, errors = validate_employee(payload)
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    db = get_db()
    if not db.execute(
        "SELECT 1 FROM departments WHERE id = ?", (data["department_id"],)
    ).fetchone():
        return jsonify(
            {
                "error": "Validation failed.",
                "fields": {"department_id": "The selected department does not exist."},
            }
        ), 400

    code = data.get("employee_code") or next_employee_code(db)
    data["employee_code"] = code

    if duplicate_email(db, data["email"]):
        return jsonify(
            {
                "error": "A record with this email already exists.",
                "fields": {"email": "This email is already registered."},
            }
        ), 409
    if duplicate_code(db, code):
        return jsonify(
            {
                "error": "A record with this employee code already exists.",
                "fields": {"employee_code": "This employee code is already in use."},
            }
        ), 409

    columns = [
        "employee_code", "first_name", "last_name", "email", "phone",
        "date_of_birth", "gender", "job_title", "department_id", "salary",
        "hire_date", "status", "address",
    ]
    placeholders = ", ".join("?" for _ in columns)
    try:
        cursor = db.execute(
            f"INSERT INTO employees ({', '.join(columns)}) VALUES ({placeholders})",
            [data[column] for column in columns],
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "The employee could not be saved. Please try again."}), 409

    invalidate_report_cache()
    created = fetch_employee(db, cursor.lastrowid)
    return jsonify({"data": employee_row(created)}), 201


@employees_bp.put("/api/employees/<int:employee_id>")
def update_employee(employee_id):
    db = get_db()
    existing = fetch_employee(db, employee_id)
    if existing is None:
        return jsonify({"error": "Employee not found."}), 404

    payload = request.get_json(silent=True)
    data, errors = validate_employee(payload, existing=existing)
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    if not db.execute(
        "SELECT 1 FROM departments WHERE id = ?", (data["department_id"],)
    ).fetchone():
        return jsonify(
            {
                "error": "Validation failed.",
                "fields": {"department_id": "The selected department does not exist."},
            }
        ), 400

    code = data.get("employee_code") or existing["employee_code"]
    if duplicate_email(db, data["email"], exclude_id=employee_id):
        return jsonify(
            {
                "error": "A record with this email already exists.",
                "fields": {"email": "This email is already registered."},
            }
        ), 409
    if duplicate_code(db, code, exclude_id=employee_id):
        return jsonify(
            {
                "error": "A record with this employee code already exists.",
                "fields": {"employee_code": "This employee code is already in use."},
            }
        ), 409

    columns = [
        "employee_code", "first_name", "last_name", "email", "phone",
        "date_of_birth", "gender", "job_title", "department_id", "salary",
        "hire_date", "status", "address",
    ]
    assignments = ", ".join(f"{column} = ?" for column in columns)
    values = [data[column] for column in columns]
    try:
        db.execute(
            f"UPDATE employees SET {assignments}, updated_at = datetime('now') "
            "WHERE id = ?",
            values + [employee_id],
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "The employee could not be updated. Please try again."}), 409

    invalidate_report_cache()
    updated = fetch_employee(db, employee_id)
    return jsonify({"data": employee_row(updated)})


@employees_bp.delete("/api/employees/<int:employee_id>")
def delete_employee(employee_id):
    """Soft delete by default; add ?hard=true for a permanent delete."""
    db = get_db()
    existing = fetch_employee(db, employee_id)
    if existing is None:
        return jsonify({"error": "Employee not found."}), 404

    hard = parse_bool(request.args.get("hard"))
    if hard:
        db.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        db.commit()
        invalidate_report_cache()
        return jsonify(
            {
                "data": employee_row(existing),
                "deleted": True,
                "hard": True,
                "soft": False,
            }
        )

    db.execute(
        "UPDATE employees SET status = 'terminated', updated_at = datetime('now') "
        "WHERE id = ?",
        (employee_id,),
    )
    db.commit()
    invalidate_report_cache()
    updated = fetch_employee(db, employee_id)
    return jsonify(
        {
            "data": employee_row(updated),
            "deleted": True,
            "hard": False,
            "soft": True,
        }
    )
