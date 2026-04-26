import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _get_key() -> bytes:
    key = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY + "==")
    if len(key) != 32:
        raise ValueError(
            f"ENCRYPTION_KEY must decode to exactly 32 bytes, got {len(key)}"
        )
    return key


def encrypt(plaintext: str) -> str:
    aesgcm = AESGCM(_get_key())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt(token: str) -> str:
    data = base64.urlsafe_b64decode(token + "==")
    nonce, ct = data[:12], data[12:]
    return AESGCM(_get_key()).decrypt(nonce, ct, None).decode()
