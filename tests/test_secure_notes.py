"""Моделі та HTTP-контракт; усі записи вигадані."""

import json
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.secure_note_repository import secure_note_repository
from app.repositories.student_repository import StudentRepository
from app.schemas.student import StudentCreate
from app.security.keys import create_process_key
from app.api.students import student_repository
import app.api.secure_notes as secure_notes_module
import app.api.crypto_lab as crypto_lab_module

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    student_repository.clear()
    secure_note_repository.clear()
    secure_notes_module.process_key = create_process_key()


def create_test_student():
    payload = {
        "full_name": "Тестовий Студент",
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "group_code": "ІП-12",  # виправлено формат відповідно до ваших схем 1-ї роботи
        "study_program": "Інженерія ПЗ",
    }
    response = client.post("/api/v1/students", json=payload)
    assert response.status_code == 201, f"Failed to create student: {response.text}"
    return response.json()["id"]


def test_unknown_student_is_not_found():
    random_id = str(uuid4())
    res = client.get(f"/api/v1/students/{random_id}/secure-notes/{uuid4()}")
    assert res.status_code == 404


def test_note_api_and_internal_storage():
    student_id = create_test_student()
    post_res = client.post(
        f"/api/v1/students/{student_id}/secure-notes",
        json={"text": "Секретний текст"},
    )
    assert post_res.status_code == 201
    note_data = post_res.json()
    note_id = note_data["id"]

    assert "text" not in note_data
    assert "key" not in note_data

    get_res = client.get(f"/api/v1/students/{student_id}/secure-notes/{note_id}")
    assert get_res.status_code == 200
    assert get_res.json()["text"] == "Секретний текст"


def test_damaged_note_is_rejected_without_plaintext():
    student_id = create_test_student()
    post_res = client.post(
        f"/api/v1/students/{student_id}/secure-notes",
        json={"text": "Тест пошкодження"},
    )
    note_id = post_res.json()["id"]

    # Штучно пошкоджуємо шифротекст у сховищі
    envelope = secure_note_repository.get_by_id(UUID(note_id))
    tampered_ct = bytes([envelope.ciphertext[0] ^ 1]) + envelope.ciphertext[1:]
    envelope.ciphertext = tampered_ct

    get_res = client.get(f"/api/v1/students/{student_id}/secure-notes/{note_id}")
    assert get_res.status_code == 500
    assert get_res.json()["detail"] == "Protected note unavailable"


def test_nonce_limit_rejects_only_new_writes():
    # Ставимо ліміт у 2 записи
    secure_notes_module.process_key = create_process_key(limit=2)
    student_id = create_test_student()

    r1 = client.post(f"/api/v1/students/{student_id}/secure-notes", json={"text": "1"})
    assert r1.status_code == 201

    r2 = client.post(f"/api/v1/students/{student_id}/secure-notes", json={"text": "2"})
    assert r2.status_code == 201

    # Третій запис має відхилятися
    r3 = client.post(f"/api/v1/students/{student_id}/secure-notes", json={"text": "3"})
    assert r3.status_code == 503

    # Старі примітки доступні для читання
    note1_id = r1.json()["id"]
    get_r1 = client.get(f"/api/v1/students/{student_id}/secure-notes/{note1_id}")
    assert get_r1.status_code == 200


def test_benchmark_report_reader(tmp_path, monkeypatch):
    report_file = tmp_path / "report.json"
    valid_data = {"schema_version": 1, "results": []}
    report_file.write_text(json.dumps(valid_data), encoding="utf-8")

    monkeypatch.setattr(crypto_lab_module, "REPORT_PATH", report_file)

    res = client.get("/api/v1/lab/crypto/benchmark-results")
    assert res.status_code == 200
    assert res.json()["schema_version"] == 1


def test_patch_secure_note_updates_text_and_uses_new_nonce():
    student_id = create_test_student()
    post_res = client.post(
        f"/api/v1/students/{student_id}/secure-notes",
        json={"text": "Початковий текст"},
    )
    note_id = post_res.json()["id"]

    # Беремо старе nonce зі сховища
    envelope_before = secure_note_repository.get_by_id(UUID(note_id))
    old_nonce = envelope_before.nonce

    # Оновлюємо примітку через PATCH
    patch_res = client.patch(
        f"/api/v1/students/{student_id}/secure-notes/{note_id}",
        json={"text": "Оновлений текст"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["text"] == "Оновлений текст"

    # Перевіряємо, що nonce змінився, а id і ключ залишилися тими самими
    envelope_after = secure_note_repository.get_by_id(UUID(note_id))
    assert envelope_after.nonce != old_nonce
    assert envelope_after.key_id == envelope_before.key_id

    # Невідоме поле у PATCH повертає 422
    bad_patch = client.patch(
        f"/api/v1/students/{student_id}/secure-notes/{note_id}",
        json={"text": "Новий", "unknown_field": "test"},
    )
    assert bad_patch.status_code == 422   


# TODO: регресійні тести всіх маршрутів роботи 1 і тест свого варіанта роботи 2.
