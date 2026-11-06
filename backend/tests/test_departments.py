"""Department CRUD and the 'cannot delete a department with employees' rule."""


def test_list_departments(seeded, client):
    body = client.get("/api/departments").get_json()
    assert body["meta"]["total"] == 5
    assert body["meta"]["total_employees"] == 25
    for row in body["data"]:
        assert row["employee_count"] == 5


def test_create_department(client):
    response = client.post(
        "/api/departments",
        json={"name": "Operations", "description": "Keeps the lights on."},
    )
    assert response.status_code == 201
    body = response.get_json()["data"]
    assert body["name"] == "Operations"
    assert body["employee_count"] == 0
    assert body["manager_name"] is None

    listed = client.get("/api/departments").get_json()
    assert listed["meta"]["total"] == 1


def test_create_department_duplicate_name(client):
    payload = {"name": "operations", "description": "Duplicate."}
    first = client.post("/api/departments", json=payload)
    second = client.post("/api/departments", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


def test_create_department_missing_name(client):
    response = client.post("/api/departments", json={"description": "No name."})
    assert response.status_code == 400
    assert "name" in response.get_json()["fields"]


def test_create_department_invalid_manager(client):
    response = client.post(
        "/api/departments", json={"name": "Operations", "manager_id": 99999}
    )
    assert response.status_code == 400
    assert "manager_id" in response.get_json()["fields"]


def test_update_department(client):
    created = client.post(
        "/api/departments", json={"name": "Operations", "description": "Old."}
    ).get_json()["data"]
    response = client.put(
        f"/api/departments/{created['id']}",
        json={"name": "Operations & Logistics", "description": "New."},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["name"] == "Operations & Logistics"


def test_update_department_duplicate_name(client):
    first = client.post("/api/departments", json={"name": "Operations"}).get_json()["data"]
    second = client.post("/api/departments", json={"name": "Logistics"}).get_json()["data"]
    response = client.put(
        f"/api/departments/{second['id']}", json={"name": "Operations"}
    )
    assert response.status_code == 409


def test_update_department_missing(client):
    response = client.put(
        "/api/departments/99999", json={"name": "Operations"}
    )
    assert response.status_code == 404


def test_delete_empty_department(client):
    created = client.post(
        "/api/departments", json={"name": "Operations"}
    ).get_json()["data"]
    response = client.delete(f"/api/departments/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["deleted"] is True
    assert client.get("/api/departments").get_json()["meta"]["total"] == 0


def test_delete_department_with_employees(seeded, client):
    engineering = client.get("/api/departments").get_json()["data"]
    engineering = next(row for row in engineering if row["name"] == "Engineering")
    response = client.delete(f"/api/departments/{engineering['id']}")
    assert response.status_code == 409
    assert "employee" in response.get_json()["error"].lower()


def test_delete_department_missing(client):
    assert client.delete("/api/departments/99999").status_code == 404
