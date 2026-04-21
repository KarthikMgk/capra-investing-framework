from fastapi.testclient import TestClient
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import User
from tests.utils.utils import random_email, random_lower_string


def test_login_success(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": settings.FIRST_SUPERUSER_PASSWORD},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "email" in data
    assert "role" in data
    assert "access_token" not in data
    assert "access_token" in r.cookies


def test_login_wrong_password(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": "incorrect"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_use_cookie(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    r = client.get(f"{settings.API_V1_STR}/auth/me", headers=superuser_token_headers)
    assert r.status_code == 200
    assert "email" in r.json()


def test_login_with_bcrypt_password_upgrades_to_argon2(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    password = random_lower_string()

    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)
    assert bcrypt_hash.startswith("$2")

    user = User(email=email, hashed_password=bcrypt_hash, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.hashed_password.startswith("$2")

    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data

    db.refresh(user)
    assert user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(password, user.hashed_password)
    assert verified
    assert updated_hash is None


def test_login_with_argon2_password_keeps_hash(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_lower_string()

    argon2_hash = get_password_hash(password)
    assert argon2_hash.startswith("$argon2")

    user = User(email=email, hashed_password=argon2_hash, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    original_hash = user.hashed_password

    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200

    db.refresh(user)
    assert user.hashed_password == original_hash
    assert user.hashed_password.startswith("$argon2")
