import base64

import pytest

from app.core.encryption import decrypt, encrypt


# AC1: encrypt then decrypt returns the original plaintext
def test_encrypt_decrypt_roundtrip() -> None:
    plaintext = "my-secret-api-key"
    assert decrypt(encrypt(plaintext)) == plaintext


# AC1: encrypted value is not equal to the input
def test_encrypt_output_differs_from_input() -> None:
    plaintext = "my-secret-api-key"
    assert encrypt(plaintext) != plaintext


# AC1: each call produces a different ciphertext (random nonce)
def test_encrypt_is_nondeterministic() -> None:
    plaintext = "same-value"
    assert encrypt(plaintext) != encrypt(plaintext)


# AC2: ValueError raised when key decodes to wrong length
def test_invalid_key_length_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    short_key = base64.urlsafe_b64encode(b"tooshort").decode()
    monkeypatch.setattr("app.core.encryption.settings.ENCRYPTION_KEY", short_key)
    with pytest.raises(ValueError, match="32 bytes"):
        encrypt("anything")
