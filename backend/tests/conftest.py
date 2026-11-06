"""Pytest fixtures.

Each test gets a fresh, empty temporary database. Tests that need records use
the `seeded` fixture, which creates them through the API. The application
itself never seeds demo data.
"""

import sqlite3

import pytest

from app import create_app
from performance import invalidate_report_cache
from test_data import DEPARTMENTS, EMPLOYEES


@pytest.fixture(autouse=True)
def clear_report_cache():
    """Reports are cached in module memory; isolate tests from each other."""
    invalidate_report_cache()
    yield
    invalidate_report_cache()


@pytest.fixture()
def app(tmp_path):
    """An empty app backed by a temporary SQLite file."""
    application = create_app(
        {
            "TESTING": True,
            "DB_PATH": str(tmp_path / "test.db"),
            "REPORT_CACHE_ENABLED": True,
            "REPORT_CACHE_TTL": 60,
            "SQLITE_WAL": True,
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    """Direct SQLite access for expected-value calculations."""
    connection = sqlite3.connect(app.config["DB_PATH"])
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    yield connection
    connection.close()


@pytest.fixture()
def seeded(client):
    """Create 5 departments and 25 employees through the API (test-only)."""
    departments = {}
    for department in DEPARTMENTS:
        response = client.post(
            "/api/departments",
            json={
                "name": department["name"],
                "description": department["description"],
            },
        )
        assert response.status_code == 201, response.get_json()
        departments[department["name"]] = response.get_json()["data"]

    employees = []
    for employee in EMPLOYEES:
        (
            code, first, last, email, phone, dob, gender, title,
            department_name, salary, hire_date, status, address,
        ) = employee
        response = client.post(
            "/api/employees",
            json={
                "employee_code": code,
                "first_name": first,
                "last_name": last,
                "email": email,
                "phone": phone,
                "date_of_birth": dob,
                "gender": gender,
                "job_title": title,
                "department_id": departments[department_name]["id"],
                "salary": salary,
                "hire_date": hire_date,
                "status": status,
                "address": address,
            },
        )
        assert response.status_code == 201, response.get_json()
        employees.append(response.get_json()["data"])

    # Assign managers after all employees exist.
    for department in DEPARTMENTS:
        manager = next(
            employee
            for employee in employees
            if employee["employee_code"] == department["manager_code"]
        )
        response = client.put(
            f"/api/departments/{departments[department['name']]['id']}",
            json={
                "name": department["name"],
                "description": department["description"],
                "manager_id": manager["id"],
            },
        )
        assert response.status_code == 200, response.get_json()
        departments[department["name"]] = response.get_json()["data"]

    return {"departments": departments, "employees": employees}


def employee_payload(**overrides):
    """A valid create payload, overridable per test."""
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
        "job_title": "QA Analyst",
        "department_id": 1,
        "hire_date": "2025-01-15",
        "salary": 50000,
        "status": "active",
        "phone": "+233 24 000 0000",
        "date_of_birth": "1995-05-05",
        "gender": "Female",
        "address": "1 Test Street, Accra",
    }
    payload.update(overrides)
    return payload
