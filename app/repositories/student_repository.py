from uuid import UUID, uuid4
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate


class EmailAlreadyExistsError(Exception):
    """Виключається, коли спроба створити або оновити студента призводить до дублювання email."""
    pass


class StudentNotFoundError(Exception):
    """Виключається, коли студента з вказаним UUID не знайдено."""
    pass


class StudentRepository:
    def __init__(self) -> None:
        self._students: dict[UUID, StudentRead] = {}

    def clear(self) -> None:
        """Очищає сховище для тестування."""
        self._students.clear()

    def create(self, student_in: StudentCreate) -> StudentRead:
        for student in self._students.values():
            if student.email.lower() == student_in.email.lower():
                raise EmailAlreadyExistsError("Студент з такою електронною адресою вже існує")

        student_id = uuid4()
        student_data = student_in.model_dump()
        student = StudentRead(id=student_id, **student_data)
        self._students[student_id] = student
        return student

    def get_all(self, study_program: str | None = None) -> list[StudentRead]:
        students = list(self._students.values())
        if study_program:
            students = [s for s in students if s.study_program == study_program]
        return students

    def get_by_id(self, student_id: UUID) -> StudentRead:
        if student_id not in self._students:
            raise StudentNotFoundError("Студента не знайдено")
        return self._students[student_id]

    def update(self, student_id: UUID, student_in: StudentUpdate) -> StudentRead:
        if student_id not in self._students:
            raise StudentNotFoundError("Студента не знайдено")

        current_student = self._students[student_id]
        update_data = student_in.model_dump(exclude_unset=True)

        if "email" in update_data:
            new_email = update_data["email"].lower()
            for s_id, student in self._students.items():
                if s_id != student_id and student.email.lower() == new_email:
                    raise EmailAlreadyExistsError("Студент з такою електронною адресою вже існує")

        updated_data = current_student.model_dump()
        updated_data.update(update_data)

        updated_student = StudentRead(**updated_data)
        self._students[student_id] = updated_student
        return updated_student


student_repository = StudentRepository()
