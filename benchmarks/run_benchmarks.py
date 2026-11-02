import json
import os
import platform
import time
from pathlib import Path

from app.security.adapters import open_bytes, seal_bytes
from app.security.profiles import BACKENDS, KEY_BYTES

# Папка для результатів
RESULTS_DIR = Path("results/practice-02")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

REPORT_JSON = RESULTS_DIR / "report.json"
REPORT_MD = RESULTS_DIR / "report.md"

PAYLOAD_SIZES = {
    "64B": 64,
    "1KB": 1024,
    "64KB": 64 * 1024,
    "1MB": 1024 * 1024,
}

ITERATIONS = 500


def run_benchmark():
    print("🚀 Запуск бенчмаркінгу криптографічних алгоритмів...")
    results = []
    nonce = b"\x00" * 12
    aad = b"benchmark-aad-context"

    for algorithm, key_len in KEY_BYTES.items():
        key = os.urandom(key_len)
        for backend in BACKENDS:
            for size_label, size_bytes in PAYLOAD_SIZES.items():
                data = os.urandom(size_bytes)

                # Замір часу шифрування (seal)
                start_seal = time.perf_counter()
                for _ in range(ITERATIONS):
                    ct, tag = seal_bytes(backend, algorithm, key, nonce, data, aad)
                seal_time_ms = ((time.perf_counter() - start_seal) / ITERATIONS) * 1000

                # Замір часу розшифрування (open)
                start_open = time.perf_counter()
                for _ in range(ITERATIONS):
                    open_bytes(backend, algorithm, key, nonce, ct, tag, aad)
                open_time_ms = ((time.perf_counter() - start_open) / ITERATIONS) * 1000

                results.append(
                    {
                        "algorithm": algorithm,
                        "backend": backend,
                        "payload_size": size_label,
                        "bytes": size_bytes,
                        "seal_time_ms": round(seal_time_ms, 5),
                        "open_time_ms": round(open_time_ms, 5),
                        "throughput_mb_s": round(
                            (size_bytes / (1024 * 1024)) / ((seal_time_ms + open_time_ms) / 1000),
                            2,
                        ),
                    }
                )

    report_data = {
        "schema_version": 1,
        "environment": {
            "python_version": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "results": results,
    }

    # Збереження JSON
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    # Збереження Markdown
    generate_markdown_report(report_data)
    print(f"✅ Звіт успішно згенеровано у {REPORT_JSON} та {REPORT_MD}")


def generate_markdown_report(data):
    md_lines = [
        "# Звіт про вимірювання продуктивності криптографічних алгоритмів",
        "",
        f"- **Система**: {data['environment']['system']} ({data['environment']['machine']})",
        f"- **Версія Python**: {data['environment']['python_version']}",
        "",
        "| Алгоритм | Бекенд | Розмір даних | Запечатування (мс) | Розпечатування (мс) | Пропускна здатність (MB/s) |",
        "|---|---|---|---|---|---|",
    ]

    for r in data["results"]:
        md_lines.append(
            f"| {r['algorithm']} | {r['backend']} | {r['payload_size']} | {r['seal_time_ms']} | {r['open_time_ms']} | {r['throughput_mb_s']} |"
        )

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


if __name__ == "__main__":
    run_benchmark()