"""Employee CRUD, validation, soft delete, and search/filter tests."""

from datetime import date, timedelta

from conftest import employee_payload


# ---------------------------------------------------------------------------
# Search, filters, sorting, pagination
# ---------------------------------------------------------------------------
def test_search_partial_case_insensitive(seeded, client):
    for term in ("kwame", "KWAME", "KwAmE"):
        response = client.get(f"/api/employees?search={term}")
        assert response.status_code == 200
        body = response.get_json()
        assert body["meta"]["total"] == 2
        assert all(
            term.lower() in " ".join(
                [row["first_name"], row["last_name"], row["email"], row["employee_code"]]
            ).lower()
            for row in body["data"]
        )


def test_search_matches_code_and_email(seeded, client):
    assert client.get("/api/employees?search=EMP-0002").get_json()["meta"]["total"] == 1
    assert client.get("/api/employees?search=akosua.boateng").get_json()["meta"]["total"] == 1


def test_search_no_results(client):
    body = client.get("/api/employees?search=zzzz-no-match").get_json()
    assert body["meta"]["total"] == 0
    assert body["data"] == []


def test_search_escapes_wildcards(client):
    body = client.get("/api/employees?search=%25").get_json()
    assert body["meta"]["total"] == 0


def test_filter_department_by_id_and_name(seeded, client):
    by_id = client.get("/api/employees?department=1").get_json()
    by_name = client.get("/api/employees?department=Engineering").get_json()
    assert by_id["meta"]["total"] == 5
    assert by_name["meta"]["total"] == 5
    assert all(row["department_name"] == "Engineering" for row in by_id["data"])


def test_filter_status(seeded, client):
    body = client.get("/api/employees?status=on_leave").get_json()
    assert body["meta"]["total"] == 4
    assert all(row["status"] == "on_leave" for row in body["data"])


def test_filter_job_title_partial(seeded, client):
    body = client.get("/api/employees?job_title=manager").get_json()
    assert body["meta"]["total"] == 5


def test_filter_hire_dates(seeded, client):
    response = client.get(
        "/api/employees?hired_from=2024-01-01&hired_to=2024-12-31"
    )
    body = response.get_json()
    assert body["meta"]["total"] == 3
    assert all("2024-01-01" <= row["hire_date"] <= "2024-12-31" for row in body["data"])


def test_filters_combined(seeded, client):
    body = client.get("/api/employees?department=1&status=active").get_json()
    assert body["meta"]["total"] == 4


def test_invalid_filter_values(client):
    assert client.get("/api/employees?status=inactive").status_code == 400
    assert client.get("/api/employees?hired_from=not-a-date").status_code == 400
    assert client.get("/api/employees?sort=password").status_code == 400
    assert client.get("/api/employees?order=sideways").status_code == 400
    assert client.get("/api/employees?page=0").status_code == 400
    assert client.get("/api/employees?per_page=0").status_code == 400


def test_pagination_counts(seeded, client):
    first = client.get("/api/employees?per_page=10&page=1").get_json()
    third = client.get("/api/employees?per_page=10&page=3").get_json()
    fourth = client.get("/api/employees?per_page=10&page=4").get_json()
    assert first["meta"]["total"] == 25
    assert first["meta"]["total_pages"] == 3
    assert len(first["data"]) == 10
    assert len(third["data"]) == 5
    assert fourth["data"] == []
    assert fourth["meta"]["total_pages"] == 3


def test_per_page_is_capped(seeded, client):
    body = client.get("/api/employees?per_page=500").get_json()
    assert body["meta"]["per_page"] == 100
    assert len(body["data"]) == 25


def test_sorting(seeded, client):
    salary = client.get("/api/employees?sort=salary&order=desc&per_page=100").get_json()
    assert salary["data"][0]["salary"] == 145000
    name = client.get("/api/employees?sort=last_name&order=asc&per_page=100").get_json()
    assert name["data"][0]["last_name"] == "Addo"


# ---------------------------------------------------------------------------
# Create + validation
# ---------------------------------------------------------------------------
def test_create_employee_auto_code(seeded, client):
    response = client.post("/api/employees", json=employee_payload())
    assert response.status_code == 201
    body = response.get_json()
    assert body["data"]["employee_code"] == "EMP-0026"
    assert body["data"]["status"] == "active"
    assert body["data"]["department_name"] == "Engineering"

    listed = client.get("/api/employees?per_page=100").get_json()
    assert listed["meta"]["total"] == 26


def test_create_employee_with_supplied_code(seeded, client):
    payload = employee_payload(employee_code="EMP-9001", email="custom@example.com")
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 201
    assert response.get_json()["data"]["employee_code"] == "EMP-9001"


def test_create_employee_missing_fields(client):
    response = client.post("/api/employees", json={"first_name": "A"})
    assert response.status_code == 400
    fields = response.get_json()["fields"]
    for field in ("last_name", "email", "job_title", "department_id", "hire_date"):
        assert field in fields


def test_create_employee_bad_email(client):
    response = client.post(
        "/api/employees", json=employee_payload(email="not-an-email")
    )
    assert response.status_code == 400
    assert "email" in response.get_json()["fields"]


def test_create_employee_future_hire_date(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    response = client.post(
        "/api/employees", json=employee_payload(hire_date=tomorrow)
    )
    assert response.status_code == 400
    assert "hire_date" in response.get_json()["fields"]


def test_create_employee_negative_salary(client):
    response = client.post("/api/employees", json=employee_payload(salary=-1))
    assert response.status_code == 400
    assert "salary" in response.get_json()["fields"]


def test_create_employee_invalid_department(client):
    response = client.post("/api/employees", json=employee_payload(department_id=999))
    assert response.status_code == 400
    assert "department_id" in response.get_json()["fields"]


def test_create_employee_duplicate_email(seeded, client):
    response = client.post(
        "/api/employees",
        json=employee_payload(email="kwame.mensah@auspify.com", employee_code="EMP-9002"),
    )
    assert response.status_code == 409


def test_create_employee_duplicate_code(seeded, client):
    response = client.post(
        "/api/employees",
        json=employee_payload(employee_code="EMP-0001", email="new-code@example.com"),
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Update + delete
# ---------------------------------------------------------------------------
def test_update_employee(seeded, client):
    created = client.post(
        "/api/employees", json=employee_payload(email="update.me@example.com")
    ).get_json()["data"]
    payload = employee_payload(
        first_name="Updated",
        last_name="Person",
        email="update.me@example.com",
        employee_code=created["employee_code"],
        salary=60000,
        status="on_leave",
    )
    response = client.put(f"/api/employees/{created['id']}", json=payload)
    assert response.status_code == 200
    body = response.get_json()["data"]
    assert body["first_name"] == "Updated"
    assert body["salary"] == 60000
    assert body["status"] == "on_leave"

    fetched = client.get(f"/api/employees/{created['id']}").get_json()["data"]
    assert fetched["first_name"] == "Updated"


def test_update_employee_duplicate_email(seeded, client):
    created = client.post(
        "/api/employees", json=employee_payload(email="duplicate-check@example.com")
    ).get_json()["data"]
    payload = employee_payload(
        email="kwame.mensah@auspify.com", employee_code=created["employee_code"]
    )
    response = client.put(f"/api/employees/{created['id']}", json=payload)
    assert response.status_code == 409


def test_update_employee_missing(client):
    response = client.put(
        "/api/employees/99999", json=employee_payload(email="missing@example.com")
    )
    assert response.status_code == 404


def test_soft_delete_hides_by_default(seeded, client):
    created = client.post(
        "/api/employees", json=employee_payload(email="soft.delete@example.com")
    ).get_json()["data"]
    response = client.delete(f"/api/employees/{created['id']}")
    assert response.status_code == 200
    body = response.get_json()
    assert body["soft"] is True
    assert body["data"]["status"] == "terminated"

    default_list = client.get("/api/employees?per_page=100").get_json()
    assert default_list["meta"]["total"] == 25
    assert all(row["id"] != created["id"] for row in default_list["data"])

    with_terminated = client.get(
        "/api/employees?include_terminated=true&per_page=100"
    ).get_json()
    assert with_terminated["meta"]["total"] == 26

    terminated = client.get("/api/employees?status=terminated").get_json()
    assert terminated["meta"]["total"] == 1
    assert terminated["data"][0]["id"] == created["id"]


def test_hard_delete(seeded, client):
    created = client.post(
        "/api/employees", json=employee_payload(email="hard.delete@example.com")
    ).get_json()["data"]
    response = client.delete(f"/api/employees/{created['id']}?hard=true")
    assert response.status_code == 200
    assert response.get_json()["hard"] is True
    assert client.get(f"/api/employees/{created['id']}").status_code == 404


def test_delete_missing_employee(client):
    assert client.delete("/api/employees/99999").status_code == 404
