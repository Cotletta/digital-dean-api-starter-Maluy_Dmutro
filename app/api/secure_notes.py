"""Каркас маршрутів приміток; не підключений до наявного app/main.py."""

from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status

from app.api.students import student_repository
from app.repositories.secure_note_repository import (
    EncryptedNoteEnvelope,
    secure_note_repository,
)
from app.repositories.student_repository import StudentNotFoundError
from app.schemas.secure_note import (
    NoteCreate,
    NoteUpdate,
    SecureNoteDetailResponse,
    SecureNoteResponse,
)
from app.security.adapters import CiphertextError, open_bytes, seal_bytes
from app.security.context import note_aad
from app.security.keys import process_key

router = APIRouter(prefix="/api/v1/students", tags=["Secure Notes"])


@router.post(
    "/{student_id}/secure-notes",
    response_model=SecureNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_secure_note(student_id: UUID, payload: NoteCreate):
    try:
        student_repository.get_by_id(student_id)
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    note_id = uuid4()
    algorithm = "AES-256-GCM"
    backend = "cryptography"

    try:
        nonce = process_key.nonces.next()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Protected note unavailable",
        )

    aad = note_aad(
        student_id=student_id,
        note_id=note_id,
        algorithm=algorithm,
        key_id=process_key.key_id,
    )

    ct, tag = seal_bytes(
        backend=backend,
        algorithm=algorithm,
        key=process_key.key,
        nonce=nonce,
        data=payload.text.encode("utf-8"),
        aad=aad,
    )

    envelope = EncryptedNoteEnvelope(
        version=1,
        student_id=student_id,
        note_id=note_id,
        algorithm=algorithm,
        backend=backend,
        key_id=process_key.key_id,
        nonce=nonce,
        ciphertext=ct,
        tag=tag,
    )

    secure_note_repository.save(envelope)

    return SecureNoteResponse(
        id=note_id,
        student_id=student_id,
        algorithm=algorithm,
    )


@router.get(
    "/{student_id}/secure-notes/{note_id}",
    response_model=SecureNoteDetailResponse,
)
def get_secure_note(student_id: UUID, note_id: UUID):
    try:
        student_repository.get_by_id(student_id)
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    envelope = secure_note_repository.get_by_id(note_id)
    if not envelope or envelope.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    if (
        envelope.version != 1
        or envelope.key_id != process_key.key_id
        or len(envelope.nonce) != 12
        or len(envelope.tag) != 16
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Protected note unavailable",
        )

    aad = note_aad(
        student_id=student_id,
        note_id=note_id,
        algorithm=envelope.algorithm,
        key_id=envelope.key_id,
    )

    try:
        pt_bytes = open_bytes(
            backend=envelope.backend,
            algorithm=envelope.algorithm,
            key=process_key.key,
            nonce=envelope.nonce,
            ct=envelope.ciphertext,
            tag=envelope.tag,
            aad=aad,
        )
        text = pt_bytes.decode("utf-8")
    except (CiphertextError, UnicodeDecodeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Protected note unavailable",
        )

    return SecureNoteDetailResponse(
        id=note_id,
        student_id=student_id,
        algorithm=envelope.algorithm,
        text=text,
    )


@router.patch(
    "/{student_id}/secure-notes/{note_id}",
    response_model=SecureNoteDetailResponse,
)
def update_secure_note(student_id: UUID, note_id: UUID, payload: NoteUpdate):
    try:
        student_repository.get_by_id(student_id)
    except StudentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    envelope = secure_note_repository.get_by_id(note_id)
    if not envelope or envelope.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    try:
        new_nonce = process_key.nonces.next()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Protected note unavailable",
        )

    aad = note_aad(
        student_id=student_id,
        note_id=note_id,
        algorithm=envelope.algorithm,
        key_id=process_key.key_id,
    )

    ct, tag = seal_bytes(
        backend=envelope.backend,
        algorithm=envelope.algorithm,
        key=process_key.key,
        nonce=new_nonce,
        data=payload.text.encode("utf-8"),
        aad=aad,
    )

    updated_envelope = EncryptedNoteEnvelope(
        version=1,
        student_id=student_id,
        note_id=note_id,
        algorithm=envelope.algorithm,
        backend=envelope.backend,
        key_id=process_key.key_id,
        nonce=new_nonce,
        ciphertext=ct,
        tag=tag,
    )

    secure_note_repository.save(updated_envelope)

    return SecureNoteDetailResponse(
        id=note_id,
        student_id=student_id,
        algorithm=envelope.algorithm,
        text=payload.text,
    )

# TODO: POST /{student_id}/secure-notes, 201 із NoteMetadata, без text і ключа.
# TODO: GET /{student_id}/secure-notes/{note_id}, 200 із перевіреним NoteRead.
# TODO: використайте наявний репозиторій студентів, не створюйте другий API.
# TODO: 404 для невідомого студента/примітки або чужого студентського ресурсу.
# TODO: 422 для неправильного UUID, тексту й невідомих полів.
# TODO: пошкоджений серверний конверт: 500, detail="Protected note unavailable".
# TODO: межа лічильника: 503 із тим самим detail; старі примітки ще читаються.
# TODO: не видавайте відкритий текст до перевірки тега і очікуваного контексту.
# TODO: один ProcessKey на процес, один NonceSequence на цей ключ.
# TODO: підключіть router у своєму main.py лише разом з реалізацією.
