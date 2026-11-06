"""Department endpoints: list with counts, create, update, delete."""

from flask import Blueprint, jsonify, request

from database import get_db
from performance import invalidate_report_cache
from validation import validate_department

departments_bp = Blueprint("departments", __name__)

DEPARTMENT_SELECT = """
    SELECT d.*,
           e.employee_code AS manager_code,
           e.first_name AS manager_first_name,
           e.last_name AS manager_last_name,
           (SELECT COUNT(*) FROM employees x WHERE x.department_id = d.id)
               AS employee_count,
           (SELECT COUNT(*) FROM employees x
             WHERE x.department_id = d.id AND x.status != 'terminated')
               AS active_employee_count
    FROM departments d
    LEFT JOIN employees e ON e.id = d.manager_id
"""


def department_row(row):
    data = dict(row)
    manager_first = data.pop("manager_first_name", None)
    manager_last = data.pop("manager_last_name", None)
    if manager_first and manager_last:
        data["manager_name"] = f"{manager_first} {manager_last}"
    else:
        data["manager_name"] = None
    return data


def fetch_department(db, department_id):
    return db.execute(
        DEPARTMENT_SELECT + "WHERE d.id = ?", (department_id,)
    ).fetchone()


def duplicate_name(db, name, exclude_id=None):
    sql = "SELECT 1 FROM departments WHERE LOWER(name) = LOWER(?)"
    params = [name]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    return db.execute(sql, params).fetchone() is not None


def manager_exists(db, manager_id):
    return db.execute(
        "SELECT 1 FROM employees WHERE id = ?", (manager_id,)
    ).fetchone() is not None


@departments_bp.get("/api/departments")
def list_departments():
    db = get_db()
    rows = db.execute(DEPARTMENT_SELECT + "ORDER BY d.name ASC").fetchall()
    data = [department_row(row) for row in rows]
    return jsonify(
        {
            "data": data,
            "meta": {
                "total": len(data),
                "total_employees": sum(item["employee_count"] for item in data),
            },
        }
    )


@departments_bp.get("/api/departments/<int:department_id>")
def get_department(department_id):
    db = get_db()
    row = fetch_department(db, department_id)
    if row is None:
        return jsonify({"error": "Department not found."}), 404
    return jsonify({"data": department_row(row)})


@departments_bp.post("/api/departments")
def create_department():
    payload = request.get_json(silent=True)
    data, errors = validate_department(payload)
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    db = get_db()
    if duplicate_name(db, data["name"]):
        return jsonify(
            {
                "error": "A department with this name already exists.",
                "fields": {"name": "This department name is already in use."},
            }
        ), 409
    if data["manager_id"] is not None and not manager_exists(db, data["manager_id"]):
        return jsonify(
            {
                "error": "Validation failed.",
                "fields": {"manager_id": "The selected manager does not exist."},
            }
        ), 400

    cursor = db.execute(
        "INSERT INTO departments (name, description, manager_id) VALUES (?, ?, ?)",
        (data["name"], data["description"], data["manager_id"]),
    )
    db.commit()
    invalidate_report_cache()
    created = fetch_department(db, cursor.lastrowid)
    return jsonify({"data": department_row(created)}), 201


@departments_bp.put("/api/departments/<int:department_id>")
def update_department(department_id):
    db = get_db()
    existing = db.execute(
        "SELECT * FROM departments WHERE id = ?", (department_id,)
    ).fetchone()
    if existing is None:
        return jsonify({"error": "Department not found."}), 404

    payload = request.get_json(silent=True)
    data, errors = validate_department(payload)
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    if duplicate_name(db, data["name"], exclude_id=department_id):
        return jsonify(
            {
                "error": "A department with this name already exists.",
                "fields": {"name": "This department name is already in use."},
            }
        ), 409
    if data["manager_id"] is not None and not manager_exists(db, data["manager_id"]):
        return jsonify(
            {
                "error": "Validation failed.",
                "fields": {"manager_id": "The selected manager does not exist."},
            }
        ), 400

    db.execute(
        "UPDATE departments SET name = ?, description = ?, manager_id = ? WHERE id = ?",
        (data["name"], data["description"], data["manager_id"], department_id),
    )
    db.commit()
    invalidate_report_cache()
    updated = fetch_department(db, department_id)
    return jsonify({"data": department_row(updated)})


@departments_bp.delete("/api/departments/<int:department_id>")
def delete_department(department_id):
    db = get_db()
    existing = db.execute(
        "SELECT * FROM departments WHERE id = ?", (department_id,)
    ).fetchone()
    if existing is None:
        return jsonify({"error": "Department not found."}), 404

    # A department with employees cannot be deleted. This also protects
    # terminated employees from an accidental cascade/restrict error.
    count = db.execute(
        "SELECT COUNT(*) AS n FROM employees WHERE department_id = ?",
        (department_id,),
    ).fetchone()["n"]
    if count:
        return jsonify(
            {
                "error": (
                    f"This department still has {count} employee(s). "
                    "Reassign or remove them before deleting."
                ),
                "employee_count": count,
            }
        ), 409

    db.execute("DELETE FROM departments WHERE id = ?", (department_id,))
    db.commit()
    invalidate_report_cache()
    return jsonify(
        {
            "data": department_row(existing),
            "deleted": True,
        }
    )
