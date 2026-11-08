from typing import Any, Literal

CONTEXT = b"digital-dean:practice-03:report-v1"

AsymmetricProfile = Literal[
    "rsa2048-oaep",
    "rsa3072-oaep",
    "rsa3072-oaep-aes256gcm",
    "hpke-x25519-aes256gcm",
    "hpke-p256-aes256gcm",
]


class ProfileInfo(dict):
    """Словник із підтримкою точкового доступу до атрибутів."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ProfileInfo' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


PROFILES: dict[str, ProfileInfo] = {
    "rsa2048-oaep": ProfileInfo(
        name="rsa2048-oaep",
        profile="rsa2048-oaep",
        key_profile="rsa-2048",
        key_type="rsa-2048",
        family="rsa",
        group="direct",
        payload_bytes=[64],
        sizes=[64],
    ),
    "rsa3072-oaep": ProfileInfo(
        name="rsa3072-oaep",
        profile="rsa3072-oaep",
        key_profile="rsa-3072",
        key_type="rsa-3072",
        family="rsa",
        group="direct",
        payload_bytes=[64],
        sizes=[64],
    ),
    "rsa3072-oaep-aes256gcm": ProfileInfo(
        name="rsa3072-oaep-aes256gcm",
        profile="rsa3072-oaep-aes256gcm",
        key_profile="rsa-3072",
        key_type="rsa-3072",
        family="rsa",
        group="hybrid",
        payload_bytes=[1024, 65536, 1048576],
        sizes=[1024, 65536, 1048576],
    ),
    "hpke-x25519-aes256gcm": ProfileInfo(
        name="hpke-x25519-aes256gcm",
        profile="hpke-x25519-aes256gcm",
        key_profile="x25519",
        key_type="x25519",
        family="hpke",
        group="hybrid",
        payload_bytes=[1024, 65536, 1048576],
        sizes=[1024, 65536, 1048576],
    ),
    "hpke-p256-aes256gcm": ProfileInfo(
        name="hpke-p256-aes256gcm",
        profile="hpke-p256-aes256gcm",
        key_profile="p256",
        key_type="p256",
        family="hpke",
        group="hybrid",
        payload_bytes=[1024, 65536, 1048576],
        sizes=[1024, 65536, 1048576],
    ),
}

KEY_PROFILES = ["rsa-2048", "rsa-3072", "x25519", "p256"]


def oaep_max_bytes(key_bits: int) -> int:
    """Гранична довжина відкритого повідомлення для RSA-OAEP із SHA-256."""
    if key_bits not in (2048, 3072):
        raise ValueError("unsupported RSA key size")
    return key_bits // 8 - 2 * 32 - 2


def expected_ciphertext_bytes(profile: str, payload_bytes: int) -> int:
    """Обчислення очікуваної довжини двійкового конверта для профілю."""
    if profile == "rsa2048-oaep":
        return 256
    elif profile == "rsa3072-oaep":
        return 384
    elif profile == "rsa3072-oaep-aes256gcm":
        return payload_bytes + 412
    elif profile == "hpke-x25519-aes256gcm":
        return payload_bytes + 48
    elif profile == "hpke-p256-aes256gcm":
        return payload_bytes + 81
    else:
        raise ValueError(f"Unknown profile: {profile}")