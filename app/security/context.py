"""Асоційовані дані пов’язують повідомлення з очікуваним ресурсом."""

import json
from uuid import UUID


def note_aad(
    student_id: UUID,
    note_id: UUID,
    algorithm: str,
    key_id: UUID,
) -> bytes:
    context = {
        "algorithm": algorithm,
        "key_id": str(key_id),
        "note_id": str(note_id),
        "student_id": str(student_id),
        "version": 1,
    }
    return json.dumps(
        context,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")