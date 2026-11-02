"""Сховище зберігає конверт, не відкритий текст і не ключ."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class EncryptedNoteEnvelope:
    version: int
    student_id: UUID
    note_id: UUID
    algorithm: str
    backend: str
    key_id: UUID
    nonce: bytes
    ciphertext: bytes
    tag: bytes


class SecureNoteRepository:
    def __init__(self) -> None:
        self._storage: dict[UUID, EncryptedNoteEnvelope] = {}

    def save(self, envelope: EncryptedNoteEnvelope) -> EncryptedNoteEnvelope:
        self._storage[envelope.note_id] = envelope
        return envelope

    def get_by_id(self, note_id: UUID) -> EncryptedNoteEnvelope | None:
        return self._storage.get(note_id)

    def clear(self) -> None:
        self._storage.clear()


secure_note_repository = SecureNoteRepository()

# TODO: додайте операції свого індивідуального варіанта.
# Підміна _items допустима лише в тестах, не через окремий HTTP-маршрут.
