from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.student_repository import student_repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_repository():
    student_repository.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_student_success():
    payload = {
        "full_name": "Іван Петренко",
        "email": "ivan.petrenko@example.com",
        "group_code": "КН-31",
        "study_program": "Комп'ютерні науки",
    }
    response = client.post("/api/v1/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["full_name"] == payload["full_name"]
    assert data["study_program"] == payload["study_program"]


def test_create_student_invalid_email():
    payload = {
        "full_name": "Іван Петренко",
        "email": "not-an-email",
        "group_code": "КН-31",
        "study_program": "Комп'ютерні науки",
    }
    response = client.post("/api/v1/students", json=payload)
    assert response.status_code == 422


def test_get_students_list():
    payload = {
        "full_name": "Іван Петренко",
        "email": "ivan.petrenko@example.com",
        "group_code": "КН-31",
        "study_program": "Комп'ютерні науки",
    }
    client.post("/api/v1/students", json=payload)

    response = client.get("/api/v1/students")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == payload["email"]


def test_get_student_by_id_success():
    payload = {
        "full_name": "Іван Петренко",
        "email": "ivan.petrenko@example.com",
        "group_code": "КН-31",
        "study_program": "Комп'ютерні науки",
    }
    create_res = client.post("/api/v1/students", json=payload)
    student_id = create_res.json()["id"]

    response = client.get(f"/api/v1/students/{student_id}")
    assert response.status_code == 200
    assert response.json()["id"] == student_id


def test_get_student_by_id_not_found():
    random_id = str(uuid4())
    response = client.get(f"/api/v1/students/{random_id}")
    assert response.status_code == 404


def test_patch_student_success():
    payload = {
        "full_name": "Іван Петренко",
        "email": "ivan.petrenko@example.com",
        "group_code": "КН-31",
        "study_program": "Комп'ютерні науки",
    }
    create_res = client.post("/api/v1/students", json=payload)
    student_id = create_res.json()["id"]

    patch_payload = {"group_code": "КН-32"}
    response = client.patch(f"/api/v1/students/{student_id}", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["group_code"] == "КН-32"
    assert data["full_name"] == "Іван Петренко"


def test_patch_student_unknown_field():
    payload = {
        "full_name": "Іван Петренко",
        "email": "ivan.petrenko@example.com",
        "group_code": "КН-31",
        "study_program": "Комп'ютерні науки",
    }
    create_res = client.post("/api/v1/students", json=payload)
    student_id = create_res.json()["id"]

    response = client.patch(
        f"/api/v1/students/{student_id}",
        json={"is_admin": True},
    )
    assert response.status_code == 422


def test_filter_by_study_program():
    student1 = {
        "full_name": "Іван Петренко",
        "email": "ivan@example.com",
        "group_code": "КН-31",
        "study_program": "Комп'ютерні науки",
    }
    student2 = {
        "full_name": "Ольга Сидоренко",
        "email": "olga@example.com",
        "group_code": "ІП-21",
        "study_program": "Інженерія програмного забезпечення",
    }
    client.post("/api/v1/students", json=student1)
    client.post("/api/v1/students", json=student2)

    response = client.get("/api/v1/students?study_program=Комп'ютерні науки")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["study_program"] == "Комп'ютерні науки"


def test_study_program_valid_boundary():
    payload = {
        "full_name": "Іван Петренко",
        "email": "ivan.petrenko@example.com",
        "group_code": "КН-31",
        "study_program": "ІТ",
    }
    response = client.post("/api/v1/students", json=payload)
    assert response.status_code == 201


def test_study_program_invalid_boundary():
    payload = {
        "full_name": "Іван Петренко",
        "email": "ivan.petrenko@example.com",
        "group_code": "КН-31",
        "study_program": "І",
    }
    response = client.post("/api/v1/students", json=payload)
    assert response.status_code == 422