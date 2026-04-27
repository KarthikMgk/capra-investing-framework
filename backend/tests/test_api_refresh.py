"""
Tests for POST /api/v1/refresh.
MockKiteClient injected via FastAPI dependency override — no real credentials.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.api.deps import get_kite_client
from app.core.exceptions import KiteAPIError
from app.main import app
from app.models.rbi_macro_data import RBIMacroData
from app.models.score_snapshot import ScoreSnapshot
from app.models.screener_data import ScreenerData
from app.schemas.stock import FactorBreakdown
from tests.conftest import MockKiteClient


def _override_kite() -> MockKiteClient:
    return MockKiteClient(session=None)


@pytest.fixture(autouse=True)
def inject_mock_kite():
    app.dependency_overrides[get_kite_client] = _override_kite
    yield
    app.dependency_overrides.pop(get_kite_client, None)


def _seed_csv_data(db: Session) -> None:
    batch_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    db.add(ScreenerData(
        upload_batch_id=batch_id, uploaded_at=now,
        symbol="HDFCBANK", pe=18.5, pb=2.8, eps=75.0,
        roe=16.5, debt_to_equity=0.9, revenue_growth=12.0, promoter_holding=26.0,
    ))
    db.add(RBIMacroData(
        upload_batch_id=batch_id, uploaded_at=now,
        repo_rate=6.5, credit_growth=14.2, liquidity_indicator=1.2,
    ))
    db.commit()


@pytest.fixture(autouse=True)
def seed_data(db: Session) -> None:
    _seed_csv_data(db)


def _admin_cookies(client: TestClient) -> dict[str, str]:
    from app.core.config import settings
    resp = client.post("/api/v1/auth/login", json={
        "email": settings.FIRST_SUPERUSER_EMAIL,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    })
    assert resp.status_code == 200
    return {"access_token": resp.cookies.get("access_token", "")}


def _viewer_cookies(client: TestClient, db: Session) -> dict[str, str]:
    from app.core.security import get_password_hash
    from app.models.user import User
    viewer = User(
        email="viewer_refresh@test.com",
        hashed_password=get_password_hash("testpass123"),
        role="viewer",
    )
    db.add(viewer)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={
        "email": "viewer_refresh@test.com", "password": "testpass123",
    })
    assert resp.status_code == 200
    return {"access_token": resp.cookies.get("access_token", "")}


def test_viewer_cannot_trigger_refresh(client: TestClient, db: Session) -> None:
    cookies = _viewer_cookies(client, db)
    resp = client.post("/api/v1/refresh", cookies=cookies)
    assert resp.status_code == 403


def test_admin_refresh_returns_200(client: TestClient) -> None:
    cookies = _admin_cookies(client)
    resp = client.post("/api/v1/refresh", cookies=cookies)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["stocks_computed"] == 50
    datetime.fromisoformat(body["computation_timestamp"].replace("Z", "+00:00"))


def test_refresh_inserts_50_rows(client: TestClient, db: Session) -> None:
    before = len(db.exec(select(ScoreSnapshot)).all())
    cookies = _admin_cookies(client)
    assert client.post("/api/v1/refresh", cookies=cookies).status_code == 200
    db.expire_all()
    assert len(db.exec(select(ScoreSnapshot)).all()) - before == 50


def test_second_refresh_appends_not_replaces(client: TestClient, db: Session) -> None:
    before = len(db.exec(select(ScoreSnapshot)).all())
    cookies = _admin_cookies(client)
    client.post("/api/v1/refresh", cookies=cookies)
    client.post("/api/v1/refresh", cookies=cookies)
    db.expire_all()
    assert len(db.exec(select(ScoreSnapshot)).all()) - before == 100


def test_latest_per_stock_query_returns_most_recent(client: TestClient, db: Session) -> None:
    cookies = _admin_cookies(client)
    client.post("/api/v1/refresh", cookies=cookies)
    r2 = client.post("/api/v1/refresh", cookies=cookies)
    ts2 = r2.json()["computation_timestamp"]
    db.expire_all()
    rows = db.exec(
        select(ScoreSnapshot)
        .where(ScoreSnapshot.stock_symbol == "HDFCBANK")
        .order_by(ScoreSnapshot.computation_timestamp.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).all()
    assert len(rows) == 1
    assert rows[0].computation_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == ts2


def test_each_row_has_non_null_audit_fields(client: TestClient, db: Session) -> None:
    cookies = _admin_cookies(client)
    client.post("/api/v1/refresh", cookies=cookies)
    db.expire_all()
    for row in db.exec(select(ScoreSnapshot)).all()[-50:]:
        assert row.factor_breakdown is not None
        assert row.kite_snapshot_ts is not None
        assert row.screener_csv_ts is not None
        assert row.rbi_csv_ts is not None


def test_factor_breakdown_schema_valid(client: TestClient, db: Session) -> None:
    cookies = _admin_cookies(client)
    client.post("/api/v1/refresh", cookies=cookies)
    db.expire_all()
    row = db.exec(
        select(ScoreSnapshot)
        .order_by(ScoreSnapshot.computation_timestamp.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()
    assert row is not None
    fb = FactorBreakdown(**row.factor_breakdown)
    assert len(fb.factors) == 9


def test_refresh_nifty_failure_returns_error(client: TestClient) -> None:
    class FailingKite(MockKiteClient):
        def get_nifty_index_prices(self, days: int) -> list[float]:
            raise KiteAPIError("Simulated Nifty fetch failure")

    app.dependency_overrides[get_kite_client] = lambda: FailingKite()
    try:
        cookies = _admin_cookies(client)
        resp = client.post("/api/v1/refresh", cookies=cookies)
        assert resp.status_code in (500, 502)
        body = resp.json(); assert "error" in body.get("detail", body)
    finally:
        app.dependency_overrides[get_kite_client] = _override_kite
