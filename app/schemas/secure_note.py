"""Моделі API відокремлені від внутрішнього криптографічного конверта."""

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=4096)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Empty note")
        if len(value.encode("utf-8")) > 4096:
            raise ValueError("Note exceeds 4096 bytes")
        return value


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=4096)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Empty note")
        if len(value.encode("utf-8")) > 4096:
            raise ValueError("Note exceeds 4096 bytes")
        return value


class SecureNoteResponse(BaseModel):
    id: UUID
    student_id: UUID
    algorithm: str


class SecureNoteDetailResponse(BaseModel):
    id: UUID
    student_id: UUID
    algorithm: str
    text: str

# TODO: виконайте індивідуальний варіант, зберігаючи базові правила.
