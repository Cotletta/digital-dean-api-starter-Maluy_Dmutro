"""Маршрут тільки читає звіт; не запускає вимірювання через HTTP."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/v1/lab/crypto", tags=["Crypto Lab"])

# Шлях за замовчуванням до файлу звіту
REPORT_PATH = Path("results/practice-02/report.json")


@router.get("/benchmark-results")
def get_benchmark_results():
    if not REPORT_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benchmark report not found",
        )

    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("schema_version") != 1 or "results" not in data:
            raise ValueError("Invalid schema")

        return data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Benchmark results unavailable",
        )


# TODO: GET /benchmark-results, 200 із повним агрегованим звітом.
# TODO: відсутній файл: 404; пошкоджений: 500 із безпечним detail.
# TODO: detail="Benchmark results unavailable", без внутрішніх шляхів.
# TODO: path беріть із конфігурації; тест підмінює конфігурацію, не HTTP-вхід.
# TODO: підключіть router у своєму main.py після реалізації.
