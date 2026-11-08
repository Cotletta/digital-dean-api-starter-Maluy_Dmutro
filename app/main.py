from fastapi import FastAPI

from app.api.asymmetric_lab import router as asymmetric_lab_router
from app.api.crypto_lab import router as crypto_lab_router
from app.api.secure_notes import router as secure_notes_router
from app.api.students import router as students_router

app = FastAPI(
    title="Digital Dean API",
    version="0.3.0",
    description="API системи Цифровий деканат",
)

app.include_router(students_router)
app.include_router(secure_notes_router)
app.include_router(crypto_lab_router)
app.include_router(asymmetric_lab_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}