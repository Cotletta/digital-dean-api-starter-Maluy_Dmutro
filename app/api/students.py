from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.repositories.student_repository import (
    EmailAlreadyExistsError,
    StudentNotFoundError,
    student_repository,
)
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/api/v1/students", tags=["students"])


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(student_in: StudentCreate) -> StudentRead:
    try:
        return student_repository.create(student_in)
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("", response_model=list[StudentRead])
def get_students(study_program: str | None = None) -> list[StudentRead]:
    return student_repository.get_all(study_program=study_program)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: UUID) -> StudentRead:
    try:
        return student_repository.get_by_id(student_id)
    except StudentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(student_id: UUID, student_in: StudentUpdate) -> StudentRead:
    if not student_in.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Необхідно передати хоча б одне поле для оновлення",
        )

    try:
        return student_repository.update(student_id, student_in)
    except StudentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )