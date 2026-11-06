"""Report endpoints and CSV exports.

Reports are read-only and cached in memory for a short time (Step 5).
Every write endpoint invalidates the cache, so a report never shows stale
data after an employee or department change.
"""

import csv
import io

from flask import Blueprint, Response, jsonify, request

from database import get_db
from performance import cached_report
from routes.employees import parse_bool
from validation import STATUSES, is_valid_date

reports_bp = Blueprint("reports", __name__)


def csv_response(filename, headers, rows):
    """Build a downloadable CSV response with an Excel-friendly BOM."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    body = "\ufeff" + output.getvalue()
    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def wants_csv():
    return request.args.get("format", "").lower() == "csv"


@reports_bp.get("/api/reports/headcount-by-department")
@cached_report
def headcount_by_department():
    db = get_db()
    rows = db.execute(
        """
        SELECT d.id AS department_id,
               d.name AS department_name,
               COUNT(e.id) AS headcount,
               COALESCE(SUM(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END), 0) AS active,
               COALESCE(SUM(CASE WHEN e.status = 'on_leave' THEN 1 ELSE 0 END), 0) AS on_leave,
               COALESCE(SUM(CASE WHEN e.status = 'terminated' THEN 1 ELSE 0 END), 0) AS terminated
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        GROUP BY d.id, d.name
        ORDER BY d.name ASC
        """
    ).fetchall()
    data = [dict(row) for row in rows]

    if wants_csv():
        return csv_response(
            "headcount-by-department.csv",
            ["Department", "Headcount", "Active", "On Leave", "Terminated"],
            [
                [row["department_name"], row["headcount"], row["active"],
                 row["on_leave"], row["terminated"]]
                for row in data
            ],
        )

    return {
        "data": data,
        "meta": {
            "total_departments": len(data),
            "total_headcount": sum(row["headcount"] for row in data),
        },
    }


@reports_bp.get("/api/reports/salary-summary")
@cached_report
def salary_summary():
    db = get_db()
    rows = db.execute(
        """
        SELECT d.id AS department_id,
               d.name AS department_name,
               COUNT(e.id) AS employee_count,
               COALESCE(MIN(e.salary), 0) AS min_salary,
               COALESCE(MAX(e.salary), 0) AS max_salary,
               COALESCE(ROUND(AVG(e.salary), 2), 0) AS average_salary,
               COALESCE(ROUND(SUM(e.salary), 2), 0) AS total_salary
        FROM departments d
        LEFT JOIN employees e
               ON e.department_id = d.id AND e.status != 'terminated'
        GROUP BY d.id, d.name
        ORDER BY d.name ASC
        """
    ).fetchall()
    data = [dict(row) for row in rows]
    total_payroll = sum(row["total_salary"] for row in data)
    total_employees = sum(row["employee_count"] for row in data)

    if wants_csv():
        return csv_response(
            "salary-summary.csv",
            ["Department", "Employees", "Minimum", "Maximum", "Average", "Total"],
            [
                [row["department_name"], row["employee_count"], row["min_salary"],
                 row["max_salary"], row["average_salary"], row["total_salary"]]
                for row in data
            ],
        )

    return {
        "data": data,
        "meta": {
            "total_employees": total_employees,
            "total_payroll": round(total_payroll, 2),
            "average_salary": round(total_payroll / total_employees, 2) if total_employees else 0,
        },
    }


@reports_bp.get("/api/reports/new-hires")
@cached_report
def new_hires():
    from_date = request.args.get("from", "").strip()
    to_date = request.args.get("to", "").strip()
    if from_date and not is_valid_date(from_date):
        return {"error": "from must use the YYYY-MM-DD format."}, 400
    if to_date and not is_valid_date(to_date):
        return {"error": "to must use the YYYY-MM-DD format."}, 400
    if from_date and to_date and from_date > to_date:
        return {"error": "from must be earlier than or equal to to."}, 400

    db = get_db()
    sql = """
        SELECT e.*, d.name AS department_name
        FROM employees e
        JOIN departments d ON d.id = e.department_id
        WHERE 1 = 1
    """
    params = []
    if from_date:
        sql += " AND e.hire_date >= ?"
        params.append(from_date)
    if to_date:
        sql += " AND e.hire_date <= ?"
        params.append(to_date)
    sql += " ORDER BY e.hire_date DESC, e.last_name ASC, e.first_name ASC"

    rows = db.execute(sql, params).fetchall()
    data = [dict(row) for row in rows]
    return {
        "from": from_date or None,
        "to": to_date or None,
        "count": len(data),
        "data": data,
    }


@reports_bp.get("/api/reports/status-breakdown")
@cached_report
def status_breakdown():
    db = get_db()
    rows = db.execute(
        "SELECT status, COUNT(*) AS count FROM employees GROUP BY status"
    ).fetchall()
    counts = {status: 0 for status in STATUSES}
    for row in rows:
        counts[row["status"]] = row["count"]
    data = [{"status": status, "count": counts[status]} for status in STATUSES]
    return {
        "data": data,
        "meta": {"total": sum(counts.values())},
    }


@reports_bp.get("/api/reports/employee-directory")
@cached_report
def employee_directory():
    include_terminated = parse_bool(request.args.get("include_terminated"))
    db = get_db()
    sql = """
        SELECT e.id, e.employee_code, e.first_name, e.last_name, e.email,
               e.phone, e.job_title, e.salary, e.hire_date, e.status,
               d.name AS department_name
        FROM employees e
        JOIN departments d ON d.id = e.department_id
    """
    if not include_terminated:
        sql += " WHERE e.status != 'terminated'"
    sql += " ORDER BY e.last_name ASC, e.first_name ASC, e.id ASC"
    rows = db.execute(sql).fetchall()
    data = [dict(row) for row in rows]

    if wants_csv():
        return csv_response(
            "employee-directory.csv",
            ["Employee Code", "First Name", "Last Name", "Email", "Phone",
             "Job Title", "Department", "Salary", "Hire Date", "Status"],
            [
                [row["employee_code"], row["first_name"], row["last_name"],
                 row["email"], row["phone"] or "", row["job_title"],
                 row["department_name"], row["salary"], row["hire_date"],
                 row["status"]]
                for row in data
            ],
        )

    return {"data": data, "meta": {"total": len(data)}}
