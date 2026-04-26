"""
Upload API endpoint tests (AC: 1, 2, 3, 4, 5, 6, 8, 9).
"""
import io
import uuid
from typing import Generator

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate
from app.models.rbi_macro_data import RBIMacroData
from app.models.screener_data import ScreenerData
from app.services.csv_validator import RBI_REQUIRED_COLUMNS, SCREENER_REQUIRED_COLUMNS

_ADMIN_EMAIL = settings.FIRST_SUPERUSER_EMAIL
_ADMIN_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD


def _make_screener_csv(rows: int = 2) -> bytes:
    data = {col: ["TEST" if col in ("Symbol", "Name") else 1.0] * rows
            for col in SCREENER_REQUIRED_COLUMNS}
    data["Symbol"] = [f"STOCK{i}" for i in range(rows)]
    return pd.DataFrame(data).to_csv(index=False).encode()


def _make_rbi_csv(rows: int = 1) -> bytes:
    data = {
        "Date": [f"2024-0{i+1}-01" for i in range(rows)],
        "Repo_Rate": [6.5] * rows,
        "Credit_Growth": [12.3] * rows,
        "Liquidity_Indicator": [0.8] * rows,
    }
    return pd.DataFrame(data).to_csv(index=False).encode()


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password},
    )
    token = r.cookies.get("access_token")
    return {"Cookie": f"access_token={token}"}


def _admin_headers(client: TestClient) -> dict[str, str]:
    return _login(client, _ADMIN_EMAIL, _ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def viewer_user(db: Session) -> Generator[User, None, None]:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email="viewer_upload_test@example.com",
            password="viewerpassword123",
            role="viewer",
        ),
    )
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture(autouse=True)
def cleanup(db: Session) -> Generator[None, None, None]:
    yield
    db.exec(delete(ScreenerData))
    db.exec(delete(RBIMacroData))
    db.commit()


# ── screener ──────────────────────────────────────────────────────────────

# AC1: valid screener upload → 201, batch_id in response
def test_upload_screener_valid(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    r = client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("screener.csv", _make_screener_csv(3), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "ok"
    assert uuid.UUID(data["batch_id"])  # valid UUID

    rows = db.exec(select(ScreenerData)).all()
    assert len(rows) == 3


# AC3: missing column → 400, CSV_COLUMN_MISSING, zero DB writes
def test_upload_screener_missing_column(client: TestClient, db: Session) -> None:
    bad_csv = b"Symbol,Name\nSTOCK1,Test\n"  # missing PE, PB, etc.
    headers = _admin_headers(client)
    r = client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("bad.csv", bad_csv, "text/csv")},
        headers=headers,
    )
    assert r.status_code == 400
    error = r.json()["error"]
    assert error["code"] == "CSV_COLUMN_MISSING"
    assert "PE" in error["details"]["expected"]
    assert "Symbol" in error["details"]["found"]

    assert db.exec(select(ScreenerData)).first() is None


# AC5: invalid upload does not touch existing data
def test_upload_screener_invalid_preserves_existing(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    # First: valid upload to seed data
    client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("screener.csv", _make_screener_csv(2), "text/csv")},
        headers=headers,
    )
    count_before = len(db.exec(select(ScreenerData)).all())
    assert count_before == 2

    # Second: invalid upload
    client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("bad.csv", b"X,Y\n1,2\n", "text/csv")},
        headers=headers,
    )
    count_after = len(db.exec(select(ScreenerData)).all())
    assert count_after == count_before


# AC6: viewer → 403 (before file processing)
def test_upload_screener_viewer_forbidden(client: TestClient, viewer_user: User) -> None:
    headers = _login(client, viewer_user.email, "viewerpassword123")
    r = client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("screener.csv", _make_screener_csv(), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 403


# AC8: second upload generates new batch_id; both batches in DB
def test_upload_screener_second_batch_appends(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    r1 = client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("s1.csv", _make_screener_csv(2), "text/csv")},
        headers=headers,
    )
    r2 = client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("s2.csv", _make_screener_csv(3), "text/csv")},
        headers=headers,
    )
    batch1 = r1.json()["batch_id"]
    batch2 = r2.json()["batch_id"]
    assert batch1 != batch2

    all_rows = db.exec(select(ScreenerData)).all()
    assert len(all_rows) == 5  # both batches present


# AC9: latest-batch query returns only second batch rows
def test_upload_screener_latest_batch_query(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("s1.csv", _make_screener_csv(2), "text/csv")},
        headers=headers,
    )
    r2 = client.post(
        f"{settings.API_V1_STR}/upload/screener",
        files={"file": ("s2.csv", _make_screener_csv(3), "text/csv")},
        headers=headers,
    )
    latest_batch_id = uuid.UUID(r2.json()["batch_id"])

    latest_rows = db.exec(
        select(ScreenerData).where(ScreenerData.upload_batch_id == latest_batch_id)
    ).all()
    assert len(latest_rows) == 3


# ── rbi ───────────────────────────────────────────────────────────────────

# AC2: valid RBI upload → 201, batch_id
def test_upload_rbi_valid(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    r = client.post(
        f"{settings.API_V1_STR}/upload/rbi",
        files={"file": ("rbi.csv", _make_rbi_csv(2), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 201
    assert uuid.UUID(r.json()["batch_id"])

    rows = db.exec(select(RBIMacroData)).all()
    assert len(rows) == 2


# AC4: RBI missing column → 400
def test_upload_rbi_missing_column(client: TestClient, db: Session) -> None:
    bad_csv = b"Date,Repo_Rate\n2024-01-01,6.5\n"
    headers = _admin_headers(client)
    r = client.post(
        f"{settings.API_V1_STR}/upload/rbi",
        files={"file": ("bad_rbi.csv", bad_csv, "text/csv")},
        headers=headers,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "CSV_COLUMN_MISSING"
    assert db.exec(select(RBIMacroData)).first() is None


# AC6: viewer → 403 on RBI endpoint too
def test_upload_rbi_viewer_forbidden(client: TestClient, viewer_user: User) -> None:
    headers = _login(client, viewer_user.email, "viewerpassword123")
    r = client.post(
        f"{settings.API_V1_STR}/upload/rbi",
        files={"file": ("rbi.csv", _make_rbi_csv(), "text/csv")},
        headers=headers,
    )
    assert r.status_code == 403
