import secrets
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hpke import AEAD, KDF, KEM, Suite

from app.security.asymmetric.profiles import CONTEXT, PROFILES, AsymmetricProfile


class DecryptionError(Exception):
    """Власний виняток для будь-яких помилок розшифрування/валідації конверта."""
    pass


def get_oaep_padding(context: bytes = CONTEXT) -> padding.OAEP:
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=context,
    )


def generate_keypair(key_type: str):
    """Генерація пари ключів за типом ключа або назвою профілю."""
    if key_type in PROFILES:
        key_type = PROFILES[key_type]["key_type"]

    if key_type in ("rsa-2048", "rsa2048-oaep", "rsa2048"):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    elif key_type in ("rsa-3072", "rsa3072-oaep", "rsa3072-oaep-aes256gcm", "rsa3072"):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    elif key_type in ("x25519", "hpke-x25519-aes256gcm"):
        private_key = x25519.X25519PrivateKey.generate()
    elif key_type in ("p256", "p-256", "hpke-p256-aes256gcm"):
        private_key = ec.generate_private_key(ec.SECP256R1())
    else:
        raise ValueError(f"Unsupported key type or profile: {key_type}")

    return private_key, private_key.public_key()


def get_hpke_suite(profile: str) -> Suite:
    if profile == "hpke-x25519-aes256gcm":
        return Suite(KEM.X25519, KDF.HKDF_SHA256, AEAD.AES_256_GCM)
    elif profile == "hpke-p256-aes256gcm":
        return Suite(KEM.P256, KDF.HKDF_SHA256, AEAD.AES_256_GCM)
    else:
        raise ValueError(f"Not an HPKE profile: {profile}")


def encrypt(
    profile: AsymmetricProfile,
    public_key,
    message: bytes,
    context: bytes = CONTEXT,
) -> bytes:
    """Шифрування повідомлення згідно з обраним профілем."""
    if profile == "rsa2048-oaep":
        if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size != 2048:
            raise ValueError("RSA-2048 public key required")
        if len(message) > 190:
            raise ValueError("Message too long for RSA-2048 OAEP")
        return public_key.encrypt(message, get_oaep_padding(context))

    elif profile == "rsa3072-oaep":
        if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size != 3072:
            raise ValueError("RSA-3072 public key required")
        if len(message) > 318:
            raise ValueError("Message too long for RSA-3072 OAEP")
        return public_key.encrypt(message, get_oaep_padding(context))

    elif profile == "rsa3072-oaep-aes256gcm":
        if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size != 3072:
            raise ValueError("RSA-3072 public key required")

        aes_key = AESGCM.generate_key(bit_length=256)
        nonce = secrets.token_bytes(12)
        wrapped_key = public_key.encrypt(aes_key, get_oaep_padding(context))
        aesgcm = AESGCM(aes_key)
        ct_with_tag = aesgcm.encrypt(nonce, message, context)
        return wrapped_key + nonce + ct_with_tag

    elif profile in ("hpke-x25519-aes256gcm", "hpke-p256-aes256gcm"):
        suite = get_hpke_suite(profile)
        return suite.encrypt(message, public_key, info=context)

    else:
        raise ValueError(f"Unknown profile: {profile}")


def decrypt(
    profile: AsymmetricProfile,
    private_key,
    ciphertext: bytes,
    context: bytes = CONTEXT,
) -> bytes:
    """Розшифрування повідомлення з обробкою всіх помилок у DecryptionError."""
    try:
        if profile == "rsa2048-oaep":
            if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size != 2048:
                raise DecryptionError("Invalid key type for profile")
            if len(ciphertext) != 256:
                raise DecryptionError("Invalid ciphertext length for RSA-2048")
            return private_key.decrypt(ciphertext, get_oaep_padding(context))

        elif profile == "rsa3072-oaep":
            if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size != 3072:
                raise DecryptionError("Invalid key type for profile")
            if len(ciphertext) != 384:
                raise DecryptionError("Invalid ciphertext length for RSA-3072")
            return private_key.decrypt(ciphertext, get_oaep_padding(context))

        elif profile == "rsa3072-oaep-aes256gcm":
            if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size != 3072:
                raise DecryptionError("Invalid key type for profile")
            if len(ciphertext) < 412:
                raise DecryptionError("Ciphertext envelope too short")

            wrapped_key = ciphertext[:384]
            nonce = ciphertext[384:396]
            ct_with_tag = ciphertext[396:]

            aes_key = private_key.decrypt(wrapped_key, get_oaep_padding(context))
            aesgcm = AESGCM(aes_key)
            return aesgcm.decrypt(nonce, ct_with_tag, context)

        elif profile in ("hpke-x25519-aes256gcm", "hpke-p256-aes256gcm"):
            suite = get_hpke_suite(profile)
            enc_len = 32 if profile == "hpke-x25519-aes256gcm" else 65
            if len(ciphertext) < enc_len + 16:
                raise DecryptionError("HPKE ciphertext too short")

            return suite.decrypt(ciphertext, private_key, info=context)

        else:
            raise DecryptionError(f"Unknown profile: {profile}")

    except Exception as e:
        if isinstance(e, DecryptionError):
            raise
        raise DecryptionError(f"Decryption failed: {str(e)}") from e