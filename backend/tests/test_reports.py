"""Report calculations, CSV exports, empty database, and cache behaviour."""

import pytest

from app import create_app
from conftest import employee_payload


def test_headcount_by_department(seeded, client):
    body = client.get("/api/reports/headcount-by-department").get_json()
    assert body["meta"]["total_departments"] == 5
    assert body["meta"]["total_headcount"] == 25
    assert len(body["data"]) == 5
    assert all(row["headcount"] == 5 for row in body["data"])
    assert sum(row["active"] for row in body["data"]) == 21
    assert sum(row["on_leave"] for row in body["data"]) == 4
    assert sum(row["terminated"] for row in body["data"]) == 0


def test_salary_summary_matches_sql(seeded, client, db):
    body = client.get("/api/reports/salary-summary").get_json()
    expected_total = db.execute(
        "SELECT COALESCE(SUM(salary), 0) FROM employees WHERE status != 'terminated'"
    ).fetchone()[0]
    assert body["meta"]["total_employees"] == 25
    assert body["meta"]["total_payroll"] == round(expected_total, 2)

    for row in body["data"]:
        expected = db.execute(
            "SELECT COUNT(*), MIN(salary), MAX(salary), AVG(salary), SUM(salary) "
            "FROM employees WHERE department_id = ? AND status != 'terminated'",
            (row["department_id"],),
        ).fetchone()
        assert row["employee_count"] == expected[0]
        assert row["min_salary"] == expected[1]
        assert row["max_salary"] == expected[2]
        assert row["average_salary"] == round(expected[3], 2)
        assert row["total_salary"] == round(expected[4], 2)


def test_new_hires_date_range(seeded, client):
    body = client.get(
        "/api/reports/new-hires?from=2024-01-01&to=2024-12-31"
    ).get_json()
    assert body["count"] == 3
    assert all("2024-01-01" <= row["hire_date"] <= "2024-12-31" for row in body["data"])
    assert body["from"] == "2024-01-01"
    assert body["to"] == "2024-12-31"


def test_new_hires_invalid_date(client):
    response = client.get("/api/reports/new-hires?from=not-a-date")
    assert response.status_code == 400


def test_status_breakdown(seeded, client):
    body = client.get("/api/reports/status-breakdown").get_json()
    counts = {row["status"]: row["count"] for row in body["data"]}
    assert counts == {"active": 21, "on_leave": 4, "terminated": 0}
    assert body["meta"]["total"] == 25


def test_employee_directory(seeded, client):
    body = client.get("/api/reports/employee-directory").get_json()
    assert body["meta"]["total"] == 25
    assert all(row["department_name"] for row in body["data"])


def test_directory_csv(seeded, client):
    response = client.get("/api/reports/employee-directory?format=csv")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert 'attachment; filename="employee-directory.csv"' in response.headers[
        "Content-Disposition"
    ]
    text = response.get_data(as_text=True)
    assert text.startswith("\ufeffEmployee Code,First Name,Last Name,Email")
    assert "Kwame,Mensah,kwame.mensah@auspify.com" in text


def test_headcount_csv(seeded, client):
    response = client.get("/api/reports/headcount-by-department?format=csv")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    text = response.get_data(as_text=True)
    assert "Department,Headcount,Active,On Leave,Terminated" in text
    assert "Engineering,5,4,1,0" in text


def test_reports_use_cache(seeded, client):
    first = client.get("/api/reports/headcount-by-department")
    assert first.headers["X-Cache"] == "MISS"
    second = client.get("/api/reports/headcount-by-department")
    assert second.headers["X-Cache"] == "HIT"
    assert second.get_json() == first.get_json()


def test_cache_invalidated_after_create(seeded, client):
    before = client.get("/api/reports/headcount-by-department").get_json()
    client.post("/api/employees", json=employee_payload(email="cache@example.com"))
    after = client.get("/api/reports/headcount-by-department")
    assert after.headers["X-Cache"] == "MISS"
    body = after.get_json()
    assert body["meta"]["total_headcount"] == before["meta"]["total_headcount"] + 1
    engineering = next(row for row in body["data"] if row["department_name"] == "Engineering")
    assert engineering["headcount"] == 6


def test_cache_invalidated_after_delete(seeded, client):
    created = client.post(
        "/api/employees", json=employee_payload(email="cache.delete@example.com")
    ).get_json()["data"]
    client.get("/api/reports/status-breakdown")
    response = client.delete(f"/api/employees/{created['id']}")
    assert response.status_code == 200
    body = client.get("/api/reports/status-breakdown").get_json()
    counts = {row["status"]: row["count"] for row in body["data"]}
    assert counts["terminated"] == 1


def test_cache_bypassed_when_disabled(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DB_PATH": str(tmp_path / "no-cache.db"),
            "SEED_ON_START": True,
            "REPORT_CACHE_ENABLED": False,
            "SQLITE_WAL": True,
        }
    )
    client = app.test_client()
    response = client.get("/api/reports/status-breakdown")
    assert response.headers["X-Cache"] == "BYPASS"


# ---------------------------------------------------------------------------
# Empty database
# ---------------------------------------------------------------------------
@pytest.fixture()
def empty_client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DB_PATH": str(tmp_path / "empty.db"),
            "SEED_ON_START": False,
            "REPORT_CACHE_ENABLED": True,
            "SQLITE_WAL": True,
        }
    )
    return app.test_client()


def test_empty_database_reports(empty_client):
    headcount = empty_client.get("/api/reports/headcount-by-department").get_json()
    assert headcount["meta"]["total_headcount"] == 0
    assert len(headcount["data"]) == 0

    salary = empty_client.get("/api/reports/salary-summary").get_json()
    assert salary["meta"]["total_employees"] == 0
    assert salary["meta"]["total_payroll"] == 0

    status = empty_client.get("/api/reports/status-breakdown").get_json()
    assert status["meta"]["total"] == 0
    assert {row["status"]: row["count"] for row in status["data"]} == {
        "active": 0,
        "on_leave": 0,
        "terminated": 0,
    }

    new_hires = empty_client.get("/api/reports/new-hires").get_json()
    assert new_hires["count"] == 0

    directory = empty_client.get("/api/reports/employee-directory").get_json()
    assert directory["meta"]["total"] == 0

    employees = empty_client.get("/api/employees").get_json()
    assert employees["meta"]["total"] == 0
    assert employees["data"] == []
