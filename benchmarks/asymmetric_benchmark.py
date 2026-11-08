import csv
import json
import os
import platform
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptography import __version__ as cryptography_version
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from app.security.asymmetric.adapters import (
    DecryptionError,
    decrypt,
    encrypt,
    generate_keypair,
)
from app.security.asymmetric.profiles import (
    CONTEXT,
    KEY_PROFILES,
    PROFILES,
    expected_ciphertext_bytes,
    oaep_max_bytes,
)

RESULTS_DIR = Path("results/practice-03")
RAW_CSV_PATH = RESULTS_DIR / "raw.csv"
REPORT_JSON_PATH = RESULTS_DIR / "report.json"


def get_git_commit() -> str:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        if len(commit) == 40:
            return commit
    except Exception:
        pass
    return "0" * 40


def measure_keygen(key_profile: str) -> tuple[float, float, int]:
    times_ns = []
    der_bytes = 0
    # Прогрів (1 раз поза вимірюванням)
    generate_keypair(key_profile)

    for _ in range(5):
        t0 = time.perf_counter_ns()
        priv, pub = generate_keypair(key_profile)
        t1 = time.perf_counter_ns()
        times_ns.append(t1 - t0)
        if der_bytes == 0:
            der_bytes = len(
                pub.public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

    med = float(statistics.median(times_ns))
    q1, _, q3 = statistics.quantiles(times_ns, n=4, method="inclusive")
    iqr = float(q3 - q1)
    return med, iqr, der_bytes


def run_checks() -> list[dict]:
    checks = []
    # 1. roundtrip, wrong_key, tamper, wrong_context (усі 5 профілів)
    for p_name, p_info in PROFILES.items():
        priv, pub = generate_keypair(p_info.key_profile)
        priv2, _ = generate_keypair(p_info.key_profile)
        msg = b"synthetic-record-check"

        # roundtrip
        try:
            ct = encrypt(p_name, pub, msg)
            dec = decrypt(p_name, priv, ct)
            checks.append({"profile": p_name, "name": "roundtrip", "passed": dec == msg})
        except Exception:
            checks.append({"profile": p_name, "name": "roundtrip", "passed": False})

        # wrong_key
        try:
            ct = encrypt(p_name, pub, msg)
            decrypt(p_name, priv2, ct)
            checks.append({"profile": p_name, "name": "wrong_key", "passed": False})
        except DecryptionError:
            checks.append({"profile": p_name, "name": "wrong_key", "passed": True})
        except Exception:
            checks.append({"profile": p_name, "name": "wrong_key", "passed": False})

        # tamper
        try:
            ct = encrypt(p_name, pub, msg)
            tampered = ct[:-1] + bytes([ct[-1] ^ 1])
            decrypt(p_name, priv, tampered)
            checks.append({"profile": p_name, "name": "tamper", "passed": False})
        except DecryptionError:
            checks.append({"profile": p_name, "name": "tamper", "passed": True})
        except Exception:
            checks.append({"profile": p_name, "name": "tamper", "passed": False})

        # wrong_context
        try:
            ct = encrypt(p_name, pub, msg, context=CONTEXT)
            decrypt(p_name, priv, ct, context=b"wrong-context")
            checks.append({"profile": p_name, "name": "wrong_context", "passed": False})
        except DecryptionError:
            checks.append({"profile": p_name, "name": "wrong_context", "passed": True})
        except Exception:
            checks.append({"profile": p_name, "name": "wrong_context", "passed": False})

    # 2. oaep_boundary (2 прямі RSA)
    for p_name, bits in [("rsa2048-oaep", 2048), ("rsa3072-oaep", 3072)]:
        priv, pub = generate_keypair(PROFILES[p_name].key_profile)
        max_len = oaep_max_bytes(bits)
        ok = True
        try:
            ct = encrypt(p_name, pub, os.urandom(max_len))
            dec = decrypt(p_name, priv, ct)
            if len(dec) != max_len:
                ok = False
        except Exception:
            ok = False

        try:
            encrypt(p_name, pub, os.urandom(max_len + 1))
            ok = False
        except ValueError:
            pass
        except Exception:
            ok = False

        checks.append({"profile": p_name, "name": "oaep_boundary", "passed": ok})

    return checks


def run_benchmark():
    print("🚀 Запуск асиметричного та гібридного бенчмаркінгу...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_rows = []
    kg_results = []
    ops_results = []

    # 1. Генерація ключів
    for kp in KEY_PROFILES:
        for s_idx in range(1, 6):
            t0 = time.perf_counter_ns()
            priv, pub = generate_keypair(kp)
            t1 = time.perf_counter_ns()
            raw_rows.append({
                "group": "key_generation",
                "profile": kp,
                "operation": "keygen",
                "payload_bytes": 0,
                "series_index": s_idx,
                "operations": 1,
                "elapsed_ns": t1 - t0,
                "ns_per_operation": float(t1 - t0),
                "ciphertext_bytes": 0,
            })

        med, iqr, der_bytes = measure_keygen(kp)
        kg_results.append({
            "key_profile": kp,
            "runs": 5,
            "median_ns": med,
            "iqr_ns": iqr,
            "public_key_der_bytes": der_bytes,
        })

    # 2. Операції Encrypt / Decrypt
    for p_name, p_info in PROFILES.items():
        priv, pub = generate_keypair(p_info.key_profile)

        for payload_size in p_info.payload_bytes:
            msg = os.urandom(payload_size)
            expected_ct_len = expected_ciphertext_bytes(p_name, payload_size)

            # --- Encrypt ---
            enc_series_averages = []
            for s_idx in range(1, 6):
                for _ in range(10):
                    encrypt(p_name, pub, msg)

                t0 = time.perf_counter_ns()
                for _ in range(20):
                    encrypt(p_name, pub, msg)
                t1 = time.perf_counter_ns()

                elapsed = t1 - t0
                avg = elapsed / 20.0
                enc_series_averages.append(avg)

                raw_rows.append({
                    "group": p_info.group,
                    "profile": p_name,
                    "operation": "encrypt",
                    "payload_bytes": payload_size,
                    "series_index": s_idx,
                    "operations": 20,
                    "elapsed_ns": elapsed,
                    "ns_per_operation": avg,
                    "ciphertext_bytes": expected_ct_len,
                })

            enc_med = float(statistics.median(enc_series_averages))
            enc_q1, _, enc_q3 = statistics.quantiles(enc_series_averages, n=4, method="inclusive")
            enc_iqr = float(enc_q3 - enc_q1)

            enc_tp = (
                round((payload_size * 10**9) / ((2**20) * enc_med), 2)
                if p_info.group == "hybrid"
                else None
            )

            ops_results.append({
                "profile": p_name,
                "group": p_info.group,
                "operation": "encrypt",
                "payload_bytes": payload_size,
                "series": 5,
                "operations_per_series": 20,
                "median_ns": enc_med,
                "iqr_ns": enc_iqr,
                "ciphertext_bytes": expected_ct_len,
                "throughput_mib_s": enc_tp,
            })

            # --- Decrypt ---
            dec_series_averages = []
            for s_idx in range(1, 6):
                cts = [encrypt(p_name, pub, msg) for _ in range(20)]

                for _ in range(10):
                    decrypt(p_name, priv, cts[0])

                t0 = time.perf_counter_ns()
                for i in range(20):
                    decrypt(p_name, priv, cts[i])
                t1 = time.perf_counter_ns()

                elapsed = t1 - t0
                avg = elapsed / 20.0
                dec_series_averages.append(avg)

                raw_rows.append({
                    "group": p_info.group,
                    "profile": p_name,
                    "operation": "decrypt",
                    "payload_bytes": payload_size,
                    "series_index": s_idx,
                    "operations": 20,
                    "elapsed_ns": elapsed,
                    "ns_per_operation": avg,
                    "ciphertext_bytes": expected_ct_len,
                })

            dec_med = float(statistics.median(dec_series_averages))
            dec_q1, _, dec_q3 = statistics.quantiles(dec_series_averages, n=4, method="inclusive")
            dec_iqr = float(dec_q3 - dec_q1)

            dec_tp = (
                round((payload_size * 10**9) / ((2**20) * dec_med), 2)
                if p_info.group == "hybrid"
                else None
            )

            ops_results.append({
                "profile": p_name,
                "group": p_info.group,
                "operation": "decrypt",
                "payload_bytes": payload_size,
                "series": 5,
                "operations_per_series": 20,
                "median_ns": dec_med,
                "iqr_ns": dec_iqr,
                "ciphertext_bytes": expected_ct_len,
                "throughput_mib_s": dec_tp,
            })

    # 3. Запис raw.csv
    fieldnames = [
        "group",
        "profile",
        "operation",
        "payload_bytes",
        "series_index",
        "operations",
        "elapsed_ns",
        "ns_per_operation",
        "ciphertext_bytes",
    ]
    with open(RAW_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(raw_rows)

    # 4. Перевірки коректності
    checks = run_checks()

    # 5. Метадані
    report_data = {
        "schema_version": 1,
        "experiment": {
            "series": 5,
            "operations_per_series": 20,
            "warmup": 10,
            "keygen_runs": 5,
            "direct_payload_bytes": 64,
            "hybrid_sizes_bytes": [1024, 65536, 1048576],
            "source_commit": get_git_commit(),
            "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "environment": {
            "python": platform.python_version(),
            "cryptography": cryptography_version,
            "openssl": default_backend().openssl_version_text(),
            "os": f"{platform.system()} {platform.release()}",
            "cpu": platform.processor() or platform.machine(),
        },
        "key_generation": kg_results,
        "results": ops_results,
        "checks": checks,
    }

    # 6. Запис report.json
    with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Бенчмаркінг завершено! Файли створено у {RESULTS_DIR}")
    print(f" - CSV: {len(raw_rows)} рядків")
    print(f" - JSON results: {len(ops_results)} записів, checks: {len(checks)} перевірок")


if __name__ == "__main__":
    run_benchmark()