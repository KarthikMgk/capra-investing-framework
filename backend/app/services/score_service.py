"""
Score Service — sole orchestrator for the full refresh cycle.

Bridges: KiteClient (I/O) + computation_engine (CPU) + DB (persistence).
No other module should import from all three layers simultaneously.

Refresh pipeline:
  Phase 1 — Concurrent async I/O via asyncio.gather (~52+ parallel Kite calls)
  Phase 2 — DB reads + per-stock CPU computation via ThreadPoolExecutor
  Phase 3 — Single-transaction bulk INSERT into score_snapshots (append-only)
"""
from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.constants import (
    FACTOR_NORMALISATION,
    NIFTY_50_SYMBOLS,
    STOCK_SECTOR_INDEX,
)
from app.core.exceptions import ComputationError
from app.models.rbi_macro_data import RBIMacroData
from app.models.score_snapshot import ScoreSnapshot
from app.models.screener_data import ScreenerData
from app.schemas.stock import FactorBreakdown
from app.services.computation_engine import (
    build_factor_breakdown,
    compute_asymmetry_index,
    compute_position_size,
    compute_relative_strength,
    compute_roc,
    compute_signal,
    compute_time_stop,
    compute_weighted_score,
)
from app.services.kite_client import KiteClient

logger = logging.getLogger(__name__)

_ROC_WINDOW = 63        # last ~3 months of trading days from 6M history
_TIME_STOP_STEP = 21    # resample daily → monthly (every 21 trading days)


@dataclass
class RefreshResult:
    stocks_computed: int
    computation_timestamp: str  # ISO 8601 UTC


# ── Normalisation ──────────────────────────────────────────────────────────────

def _norm(factor: str, raw: float | None) -> float:
    """Map raw factor value to [-1, +1] using FACTOR_NORMALISATION ranges."""
    if raw is None:
        return 0.0
    low, high, invert = FACTOR_NORMALISATION[factor]
    if high == low:
        return 0.0
    score = 2.0 * (raw - low) / (high - low) - 1.0
    clamped = max(-1.0, min(1.0, score))
    return -clamped if invert else clamped


# ── Beta ───────────────────────────────────────────────────────────────────────

def _compute_beta(stock_prices: list[float], nifty_prices: list[float]) -> float:
    """Compute stock beta vs Nifty from daily closing prices."""
    n = min(len(stock_prices), len(nifty_prices)) - 1
    if n < 5:
        return 1.0
    s_ret = [(stock_prices[i + 1] - stock_prices[i]) / stock_prices[i] for i in range(n)]
    n_ret = [(nifty_prices[i + 1] - nifty_prices[i]) / nifty_prices[i] for i in range(n)]
    s_mean = sum(s_ret) / n
    n_mean = sum(n_ret) / n
    cov = sum((s - s_mean) * (nx - n_mean) for s, nx in zip(s_ret, n_ret)) / (n - 1)
    var_n = sum((x - n_mean) ** 2 for x in n_ret) / (n - 1)
    if var_n < 1e-10:
        return 1.0
    return max(0.1, cov / var_n)


# ── Per-stock computation (sync, runs in ThreadPoolExecutor) ──────────────────

def _compute_stock(
    symbol: str,
    prices_6m: list[float],
    nifty_prices_6m: list[float],
    usdinr_prices_6m: list[float],
    gold_prices_6m: list[float],
    sector_prices_6m: list[float],
    screener: dict | None,
    rbi: dict,
) -> dict:
    """
    Compute all framework scores for one stock.
    Pure sync — no I/O. All data pre-loaded and passed as plain dicts.
    3-month ROC: last 63 entries of 6M daily series (~63 trading days).
    Time Stop: resampled to monthly via prices_6m[::21].
    """
    # Guard: if price data is missing use neutral scores
    if len(prices_6m) < 2:
        logger.warning("No price data for %s — all price-derived factors = 0.0", symbol)
        prices_6m = [100.0, 100.0]
    if len(nifty_prices_6m) < 2:
        nifty_prices_6m = [100.0, 100.0]

    def _ret(prices: list[float]) -> float:
        if len(prices) < 2 or prices[0] == 0:
            return 0.0
        return (prices[-1] - prices[0]) / prices[0]

    nifty_ret = _ret(nifty_prices_6m)
    usdinr_ret = _ret(usdinr_prices_6m)
    gold_ret = _ret(gold_prices_6m)
    sector_ret = _ret(sector_prices_6m)

    rs_ratio = compute_relative_strength(prices_6m, nifty_prices_6m)

    factors = {
        "liquidity":         _norm("liquidity",         rbi.get("liquidity_indicator")),
        "rates":             _norm("rates",             rbi.get("repo_rate")),
        "credit_growth":     _norm("credit_growth",     rbi.get("credit_growth")),
        "valuation":         _norm("valuation",         screener.get("pe") if screener else None),
        "earnings":          _norm("earnings",          screener.get("roe") if screener else None),
        "relative_strength": _norm("relative_strength", rs_ratio),
        "usd_lens":          _norm("usd_lens",          nifty_ret - usdinr_ret),
        "gold_lens":         _norm("gold_lens",         nifty_ret - gold_ret),
        "sector_strength":   _norm("sector_strength",   sector_ret - nifty_ret),
    }

    composite_score = compute_weighted_score(factors)
    roc_series = prices_6m[-_ROC_WINDOW:] if len(prices_6m) >= _ROC_WINDOW else prices_6m
    roc = compute_roc(roc_series)
    asymmetry_index = compute_asymmetry_index(
        valuation_score=factors["valuation"],
        earnings_score=factors["earnings"],
        liquidity_score=factors["liquidity"],
    )
    signal = compute_signal(composite_score, roc, asymmetry_index)
    beta = _compute_beta(prices_6m, nifty_prices_6m)
    position_breakdown = compute_position_size(signal, composite_score, beta)

    monthly_prices = prices_6m[::_TIME_STOP_STEP]
    time_stop_months = compute_time_stop(monthly_prices)

    factor_breakdown = build_factor_breakdown(
        factors=factors,
        roc=roc,
        asymmetry_index=asymmetry_index,
        time_stop_months=time_stop_months,
        position_breakdown=position_breakdown,
    )
    FactorBreakdown(**factor_breakdown)  # validate JSONB schema before write

    return {
        "stock_symbol": symbol,
        "composite_score": composite_score,
        "signal": signal,
        "position_size": position_breakdown["final_pct"],
        "factor_breakdown": factor_breakdown,
    }


# ── Phase 1: Concurrent I/O ────────────────────────────────────────────────────

def _safe_usdinr(kite_client: KiteClient) -> list[float]:
    """Fetch USDINR prices, returning [] if CDS segment is not activated."""
    try:
        return kite_client.get_usdinr_prices(180)
    except Exception as exc:
        logger.warning("USDINR fetch failed (CDS not activated?): %s — usd_lens = 0.0", exc)
        return []


async def _fetch_all_market_data(
    kite_client: KiteClient,
) -> tuple[dict[str, list[float]], list[float], list[float], list[float], dict[str, list[float]]]:
    unique_sectors = sorted({
        STOCK_SECTOR_INDEX[s] for s in NIFTY_50_SYMBOLS if s in STOCK_SECTOR_INDEX
    })

    coros: list = []
    for symbol in NIFTY_50_SYMBOLS:
        coros.append(asyncio.to_thread(kite_client.get_historical_prices, symbol, 180))
    n = len(NIFTY_50_SYMBOLS)
    coros.append(asyncio.to_thread(kite_client.get_nifty_index_prices, 180))   # n
    coros.append(asyncio.to_thread(_safe_usdinr, kite_client))                 # n+1
    coros.append(asyncio.to_thread(kite_client.get_gold_prices, 180))          # n+2
    for sector in unique_sectors:
        coros.append(asyncio.to_thread(kite_client.get_sector_prices, sector, 180))  # n+3+i

    results = await asyncio.gather(*coros, return_exceptions=True)

    def _unwrap(idx: int, label: str) -> list[float]:
        r = results[idx]
        if isinstance(r, Exception):
            logger.warning("%s fetch failed: %s — neutral fallback", label, r)
            return []
        return r  # type: ignore[return-value]

    stock_prices_map = {
        symbol: (_unwrap(i, symbol))
        for i, symbol in enumerate(NIFTY_50_SYMBOLS)
    }
    nifty_prices = _unwrap(n, "Nifty index")
    usdinr_prices = _unwrap(n + 1, "USDINR")
    gold_prices = _unwrap(n + 2, "Gold/GOLDBEES")
    sector_prices_map = {
        sector: _unwrap(n + 3 + j, f"Sector:{sector}")
        for j, sector in enumerate(unique_sectors)
    }

    if not nifty_prices:
        from app.core.exceptions import KiteAPIError
        raise KiteAPIError("Nifty 50 price fetch failed — cannot compute relative strength")

    return stock_prices_map, nifty_prices, usdinr_prices, gold_prices, sector_prices_map


# ── Phase 2a: DB reads ────────────────────────────────────────────────────────

def _load_screener_data(session: Session) -> tuple[dict[str, dict], datetime]:
    latest = session.exec(
        select(ScreenerData.upload_batch_id, ScreenerData.uploaded_at)
        .order_by(ScreenerData.uploaded_at.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()
    if not latest:
        raise ComputationError("No screener CSV found. Upload Screener.in data first.")

    batch_id, csv_ts = latest
    rows = session.exec(
        select(ScreenerData).where(ScreenerData.upload_batch_id == batch_id)
    ).all()
    screener_map = {
        row.symbol: {k: getattr(row, k) for k in ("pe", "pb", "eps", "roe",
                     "debt_to_equity", "revenue_growth", "promoter_holding")}
        for row in rows
    }
    return screener_map, csv_ts


def _load_rbi_data(session: Session) -> tuple[dict, datetime]:
    latest = session.exec(
        select(RBIMacroData)
        .order_by(RBIMacroData.uploaded_at.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()
    if not latest:
        raise ComputationError("No RBI macro CSV found. Upload RBI data first.")

    return {
        "repo_rate": latest.repo_rate,
        "credit_growth": latest.credit_growth,
        "liquidity_indicator": latest.liquidity_indicator,
    }, latest.uploaded_at


# ── Phase 3: DB write ─────────────────────────────────────────────────────────

def _write_snapshots(
    session: Session,
    computed_rows: list[dict],
    kite_snapshot_ts: datetime,
    screener_csv_ts: datetime,
    rbi_csv_ts: datetime,
    computation_ts: datetime,
) -> None:
    try:
        for row in computed_rows:
            session.add(ScoreSnapshot(
                stock_symbol=row["stock_symbol"],
                composite_score=row["composite_score"],
                signal=row["signal"],
                position_size=row["position_size"],
                computation_timestamp=computation_ts,
                kite_snapshot_ts=kite_snapshot_ts,
                screener_csv_ts=screener_csv_ts,
                rbi_csv_ts=rbi_csv_ts,
                factor_breakdown=row["factor_breakdown"],
            ))
        session.commit()
        logger.info("Committed %d snapshots at %s", len(computed_rows), computation_ts.isoformat())
    except Exception:
        session.rollback()
        logger.error("DB write failed — rolled back all rows", exc_info=True)
        raise


# ── Entry point ───────────────────────────────────────────────────────────────

async def run_full_refresh(session: Session, kite_client: KiteClient) -> RefreshResult:
    """
    Full Capra refresh: fetch → compute → persist.
    Raises KiteAPIError, ComputationError, or DB exceptions. Never HTTPException.
    """
    logger.info("Starting full refresh for %d stocks", len(NIFTY_50_SYMBOLS))

    stock_prices_map, nifty_prices, usdinr_prices, gold_prices, sector_prices_map = (
        await _fetch_all_market_data(kite_client)
    )
    kite_snapshot_ts = datetime.now(timezone.utc)

    screener_map, screener_csv_ts = _load_screener_data(session)
    rbi_dict, rbi_csv_ts = _load_rbi_data(session)
    computation_ts = datetime.now(timezone.utc)

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            loop.run_in_executor(
                executor, _compute_stock,
                symbol,
                stock_prices_map.get(symbol, []),
                nifty_prices,
                usdinr_prices,
                gold_prices,
                sector_prices_map.get(STOCK_SECTOR_INDEX.get(symbol, ""), []),
                screener_map.get(symbol),
                rbi_dict,
            )
            for symbol in NIFTY_50_SYMBOLS
        ]
        computed_rows: list[dict] = list(await asyncio.gather(*futures))

    _write_snapshots(session, computed_rows, kite_snapshot_ts,
                     screener_csv_ts, rbi_csv_ts, computation_ts)

    return RefreshResult(
        stocks_computed=len(computed_rows),
        computation_timestamp=computation_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
