"""Параметри визначеного навчального профілю, не універсальні межі схем."""

BACKENDS = ("cryptography", "pycryptodome")

KEY_BYTES = {
    "AES-128-GCM": 16,
    "AES-256-GCM": 32,
    "ChaCha20-Poly1305": 32,
}


def validate_profile(algorithm: str, key: bytes, nonce: bytes) -> None:
    if algorithm not in KEY_BYTES:
        raise ValueError("Unsupported algorithm")
    if len(key) != KEY_BYTES[algorithm]:
        raise ValueError("Invalid key length")
    if len(nonce) != 12:
        raise ValueError("Invalid nonce length")