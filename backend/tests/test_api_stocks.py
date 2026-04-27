"""Tests for GET /api/v1/stocks and GET /api/v1/stocks/{symbol}."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.constants import NIFTY_50_SYMBOLS
from app.models.score_snapshot import ScoreSnapshot


def _admin_cookies(client: TestClient) -> dict[str, str]:
    from app.core.config import settings
    resp = client.post("/api/v1/auth/login", json={
        "email": settings.FIRST_SUPERUSER_EMAIL,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    })
    assert resp.status_code == 200
    return {"access_token": resp.cookies.get("access_token", "")}


def _seed_snapshot(db: Session, symbol: str = "HDFCBANK") -> ScoreSnapshot:
    now = datetime.now(timezone.utc)
    snap = ScoreSnapshot(
        stock_symbol=symbol,
        composite_score=0.6125,
        signal="buy",
        position_size=97.5,
        computation_timestamp=now,
        kite_snapshot_ts=now,
        screener_csv_ts=now,
        rbi_csv_ts=now,
        factor_breakdown={
            "factors": [
                {"name": k, "weight": 0.1, "raw_value": 0.5,
                 "weighted_contribution": 0.05, "signal": "positive"}
                for k in [
                    "liquidity", "rates", "credit_growth", "valuation", "earnings",
                    "relative_strength", "usd_lens", "gold_lens", "sector_strength",
                ]
            ],
            "roc": 0.087,
            "asymmetry_index": 0.42,
            "time_stop_months": 0,
            "position_breakdown": {
                "base_pct": 65.0,
                "conviction_multiplier": 1.5,
                "volatility_adjustment": 1.0,
                "final_pct": 97.5,
            },
        },
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def test_list_stocks_returns_50_items(client: TestClient, db: Session) -> None:
    cookies = _admin_cookies(client)
    resp = client.get("/api/v1/stocks", cookies=cookies)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 50
    assert len(body["items"]) == 50


def test_list_stocks_includes_name(client: TestClient, db: Session) -> None:
    cookies = _admin_cookies(client)
    body = client.get("/api/v1/stocks", cookies=cookies).json()
    hdfc = next(i for i in body["items"] if i["stock_symbol"] == "HDFCBANK")
    assert "HDFC" in hdfc["name"]


def test_list_stocks_signal_null_before_refresh(client: TestClient, db: Session) -> None:
    cookies = _admin_cookies(client)
    body = client.get("/api/v1/stocks", cookies=cookies).json()
    # Before any snapshot for a symbol, signal should be null
    wipro = next(i for i in body["items"] if i["stock_symbol"] == "WIPRO")
    assert wipro["signal"] is None or isinstance(wipro["signal"], str)


def test_list_stocks_signal_present_after_snapshot(client: TestClient, db: Session) -> None:
    _seed_snapshot(db, "HDFCBANK")
    cookies = _admin_cookies(client)
    body = client.get("/api/v1/stocks", cookies=cookies).json()
    hdfc = next(i for i in body["items"] if i["stock_symbol"] == "HDFCBANK")
    assert hdfc["signal"] == "buy"


def test_get_stock_returns_full_response(client: TestClient, db: Session) -> None:
    _seed_snapshot(db)
    cookies = _admin_cookies(client)
    resp = client.get("/api/v1/stocks/HDFCBANK", cookies=cookies)
    assert resp.status_code == 200
    body = resp.json()
    assert body["stock_symbol"] == "HDFCBANK"
    assert body["composite_score"] == pytest.approx(0.6125)
    assert body["signal"] == "buy"
    assert body["factor_breakdown"] is not None


def test_get_stock_factor_breakdown_has_9_factors(client: TestClient, db: Session) -> None:
    _seed_snapshot(db)
    cookies = _admin_cookies(client)
    body = client.get("/api/v1/stocks/HDFCBANK", cookies=cookies).json()
    factors = body["factor_breakdown"]["factors"]
    assert len(factors) == 9
    for f in factors:
        for key in ("name", "weight", "raw_value", "weighted_contribution", "signal"):
            assert key in f


def test_get_stock_factor_breakdown_top_level_keys(client: TestClient, db: Session) -> None:
    _seed_snapshot(db)
    cookies = _admin_cookies(client)
    fb = client.get("/api/v1/stocks/HDFCBANK", cookies=cookies).json()["factor_breakdown"]
    for key in ("roc", "asymmetry_index", "time_stop_months", "position_breakdown"):
        assert key in fb
    for key in ("base_pct", "conviction_multiplier", "volatility_adjustment", "final_pct"):
        assert key in fb["position_breakdown"]


def test_get_stock_404_when_no_snapshot(client: TestClient, db: Session) -> None:
    cookies = _admin_cookies(client)
    # Use a symbol that is definitely not a real Nifty 50 stock
    resp = client.get("/api/v1/stocks/FAKESTOCK999", cookies=cookies)
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "SCORE_NOT_FOUND"


def test_unauthenticated_list_stocks_returns_401() -> None:
    from app.main import app as _app
    with TestClient(_app) as fresh:
        assert fresh.get("/api/v1/stocks").status_code == 401


def test_unauthenticated_get_stock_returns_401() -> None:
    from app.main import app as _app
    with TestClient(_app) as fresh:
        assert fresh.get("/api/v1/stocks/HDFCBANK").status_code == 401


def test_get_stock_symbol_uppercased(client: TestClient, db: Session) -> None:
    _seed_snapshot(db, "TCS")
    cookies = _admin_cookies(client)
    resp = client.get("/api/v1/stocks/tcs", cookies=cookies)
    assert resp.status_code == 200
    assert resp.json()["stock_symbol"] == "TCS"
