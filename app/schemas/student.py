from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class StudentCreate(StrictModel):
    full_name: str = Field(min_length=5, max_length=120)
    email: EmailStr
    group_code: str = Field(pattern=r"^[A-ZА-ЩЬЮЯЇІЄҐ0-9]+-[0-9]{2}$")
    study_program: str = Field(min_length=2, max_length=100)


class StudentRead(StudentCreate):
    id: UUID


class StudentUpdate(StrictModel):
    full_name: str | None = Field(default=None, min_length=5, max_length=120)
    email: EmailStr | None = None
    group_code: str | None = Field(default=None, pattern=r"^[A-ZА-ЩЬЮЯЇІЄҐ0-9]+-[0-9]{2}$")
    study_program: str | None = Field(default=None, min_length=2, max_length=100)