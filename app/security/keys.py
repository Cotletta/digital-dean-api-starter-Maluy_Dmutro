"""Матеріал ключа створюють один раз під час запуску процесу API."""

import secrets
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.security.nonce import NonceSequence


@dataclass(frozen=True)
class ProcessKey:
    key_id: UUID
    key: bytes = field(repr=False)
    nonces: NonceSequence = field(repr=False)


def create_process_key(limit: int = 1_000_000) -> ProcessKey:
    return ProcessKey(
        key_id=uuid4(),
        key=secrets.token_bytes(32),
        nonces=NonceSequence(limit=limit),
    )


process_key = create_process_key()

MASTER_KEY = process_key.key
MASTER_KEY_ID = process_key.key_id
nonce_sequence = process_key.nonces
# TODO: збережіть один ProcessKey у стані застосунку/його залежностях.
# TODO: маршрути запису й читання використовують цей самий матеріал ключа.
# Не зберігайте ключ у репозиторії приміток, файлі, JSON чи Git.
