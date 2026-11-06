"""Health, empty-database, and fixture smoke tests."""

import pytest

from app import create_app


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["service"] == "Auspify EMS API"


def test_app_starts_empty(client):
    """The application must not contain demo/seed records."""
    departments = client.get("/api/departments").get_json()
    employees = client.get("/api/employees").get_json()
    assert departments["meta"]["total"] == 0
    assert departments["data"] == []
    assert employees["meta"]["total"] == 0
    assert employees["data"] == []


def test_seeded_fixture_creates_data(seeded):
    """The test-only fixture creates 5 departments and 25 employees."""
    departments = seeded["departments"]
    employees = seeded["employees"]
    assert len(departments) == 5
    assert len(employees) == 25
    engineering = departments["Engineering"]
    assert engineering["manager_name"] == "Kwame Mensah"
    assert engineering["employee_count"] == 5


def test_foreign_keys_enabled(db):
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_wal_mode(db):
    assert db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_foreign_key_rejects_invalid_department(db):
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO employees (employee_code, first_name, last_name, email, "
            "job_title, department_id, salary, hire_date) "
            "VALUES ('EMP-X', 'A', 'B', 'a@b.com', 'Dev', 999, 1, '2025-01-01')"
        )


def test_no_seed_on_start(tmp_path):
    """A second app instance also starts with an empty database."""
    app = create_app(
        {
            "TESTING": True,
            "DB_PATH": str(tmp_path / "empty.db"),
            "REPORT_CACHE_ENABLED": True,
            "SQLITE_WAL": True,
        }
    )
    client = app.test_client()
    assert client.get("/api/departments").get_json()["meta"]["total"] == 0
    assert client.get("/api/employees").get_json()["meta"]["total"] == 0
