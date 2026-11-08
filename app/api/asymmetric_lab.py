import json
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.asymmetric_report import BenchmarkReport, BenchmarkResponse
from app.security.asymmetric.profiles import AsymmetricProfile

router = APIRouter(prefix="/api/v1/lab/crypto", tags=["Crypto Lab"])
REPORT_PATH = Path("results/practice-03/report.json")
MAX_REPORT_BYTES = 1048576


def dict_raise_on_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Перевірка та відмова при наявності дублікатів ключів у JSON."""
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"Duplicate key found: {k}")
        d[k] = v
    return d


def reject_json_constants(val: str) -> Any:
    """Відмова при виявленні нечислових констант NaN, Infinity."""
    raise ValueError(f"Invalid JSON constant: {val}")


def load_report(path: Path | str | None = None) -> BenchmarkReport:
    """Зчитування, перевірка розміру та валідація JSON-звіту."""
    target_path = REPORT_PATH if path is None else Path(path)

    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="benchmark report not found",
        )

    try:
        with open(target_path, "rb") as f:
            content = f.read(MAX_REPORT_BYTES + 1)

        if len(content) > MAX_REPORT_BYTES:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="benchmark report invalid",
            )

        text = content.decode("utf-8")
        raw_data = json.loads(
            text,
            object_pairs_hook=dict_raise_on_duplicates,
            parse_constant=reject_json_constants,
        )

        return BenchmarkReport.model_validate(raw_data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="benchmark report invalid",
        )


@router.get(
    "/asymmetric-benchmark-results",
    response_model=BenchmarkResponse,
    status_code=status.HTTP_200_OK,
)
def get_asymmetric_benchmark_results(
    profile: AsymmetricProfile | None = Query(default=None)
):
    """Отримання результатів бенчмаркінгу з підтримкою фільтрації за профілем (Варіант 0)."""
    report = load_report()
    response_data = report.model_dump()

    if profile is not None:
        response_data["results"] = [
            item for item in response_data["results"] if item["profile"] == profile
        ]

    return response_data