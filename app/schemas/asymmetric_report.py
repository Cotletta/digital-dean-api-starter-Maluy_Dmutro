from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.security.asymmetric.profiles import AsymmetricProfile


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    series: int = Field(default=5)
    operations_per_series: int = Field(default=20)
    warmup: int = Field(default=10)
    keygen_runs: int = Field(default=5)
    direct_payload_bytes: int = Field(default=64)
    hybrid_sizes_bytes: list[int] = Field(default=[1024, 65536, 1048576])
    source_commit: str = Field(min_length=40, max_length=40)
    created_at_utc: str = Field(...)


ExperimentMeta = Experiment


class Environment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    python: str
    cryptography: str
    openssl: str
    os: str
    cpu: str


EnvironmentMeta = Environment


class KeyGenerationItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    key_profile: str
    runs: int = Field(default=5)
    median_ns: float = Field(gt=0, allow_inf_nan=False)
    iqr_ns: float = Field(ge=0, allow_inf_nan=False)
    public_key_der_bytes: int = Field(gt=0)


class ResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    profile: AsymmetricProfile
    group: Literal["direct", "hybrid"]
    operation: Literal["encrypt", "decrypt"]
    payload_bytes: int = Field(gt=0, le=1048576)
    series: int = Field(default=5)
    operations_per_series: int = Field(default=20)
    median_ns: float = Field(gt=0, allow_inf_nan=False)
    iqr_ns: float = Field(ge=0, allow_inf_nan=False)
    ciphertext_bytes: int = Field(gt=0)
    throughput_mib_s: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class CheckItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    profile: AsymmetricProfile
    name: str
    passed: bool


class BenchmarkReport(BaseModel):
    """Повна базова модель для перевірки згенерованого report.json (22 results / 22 checks)."""
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1]
    experiment: Experiment
    environment: Environment
    key_generation: list[KeyGenerationItem] = Field(min_length=4, max_length=4)
    results: list[ResultItem] = Field(min_length=22, max_length=22)
    checks: list[CheckItem] = Field(min_length=22, max_length=22)


class BenchmarkResponse(BaseModel):
    """Модель відповіді API (дозволяє фільтрацію results від 0 до 22 елементів)."""
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1]
    experiment: Experiment
    environment: Environment
    key_generation: list[KeyGenerationItem]
    results: list[ResultItem]
    checks: list[CheckItem]