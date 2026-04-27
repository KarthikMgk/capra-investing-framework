"""
Pure computation functions for the Multi-Layer Capital Allocation System v3.0.

PURITY CONTRACT: no I/O, no database, no HTTP, no framework imports.
Every function is callable with plain Python dicts and lists.
All constants come from app.core.constants — zero numeric literals here.
"""
from __future__ import annotations

import math

from app.core.constants import (
    ASYMMETRY_NEG_THRESHOLD,
    ASYMMETRY_POS_THRESHOLD,
    CONVICTION_MULTIPLIER_TABLE,
    DECISION_MATRIX,
    FACTOR_WEIGHTS,
    MEANINGFUL_MOVEMENT_THRESHOLD,
    MOMENTUM_DOWN_THRESHOLD,
    MOMENTUM_UP_THRESHOLD,
    POSITION_BASE_TABLE,
    SCORE_HIGH_THRESHOLD,
    SCORE_LOW_THRESHOLD,
    VOLATILITY_ADJUSTMENT,
)


# ── Weighted composite score ───────────────────────────────────────────────────

def compute_weighted_score(factors: dict[str, float]) -> float:
    """
    Compute weighted composite score from pre-normalised factor values.

    factors: dict keyed by factor name (must match FACTOR_WEIGHTS exactly),
             values in [-1, +1] range.
    Returns: weighted sum clamped to [-1, +1], rounded to 4 decimal places.
    Raises: ValueError if any FACTOR_WEIGHTS key is missing from factors.
    """
    missing = set(FACTOR_WEIGHTS) - set(factors)
    if missing:
        raise ValueError(f"Missing factor(s): {sorted(missing)}")

    total = sum(factors[name] * weight for name, weight in FACTOR_WEIGHTS.items())
    clamped = max(-1.0, min(1.0, total))
    return round(clamped, 4)


# ── Rate of change (3-month momentum) ─────────────────────────────────────────

def compute_roc(prices_3m: list[float]) -> float:
    """
    Compute 3-month rate of change: (last - first) / first.

    prices_3m: ordered price series (oldest first, most recent last),
               minimum 2 elements.
    Returns: ROC as a decimal (e.g. 0.10 = +10%).
    Raises: ValueError if list has fewer than 2 elements.
    """
    if len(prices_3m) < 2:
        raise ValueError(
            f"prices_3m must have at least 2 elements, got {len(prices_3m)}"
        )
    first, last = prices_3m[0], prices_3m[-1]
    if first == 0:
        raise ValueError("First price in series is zero — cannot compute ROC")
    return (last - first) / first


# ── Asymmetry Index ───────────────────────────────────────────────────────────

def compute_asymmetry_index(
    valuation_score: float,
    earnings_score: float,
    liquidity_score: float,
) -> float:
    """
    Asymmetry = (-Valuation) + Earnings + Liquidity.

    Measures risk/reward asymmetry: expensive + weak earnings + tight liquidity
    gives a negative result; cheap + strong earnings + loose liquidity is positive.
    """
    return (-valuation_score) + earnings_score + liquidity_score


# ── Signal classification ─────────────────────────────────────────────────────

def _bucket_score(score: float) -> str:
    if score > SCORE_HIGH_THRESHOLD:
        return "high"
    if score < SCORE_LOW_THRESHOLD:
        return "low"
    return "mid"


def _bucket_momentum(roc: float) -> str:
    if roc > MOMENTUM_UP_THRESHOLD:
        return "up"
    if roc < MOMENTUM_DOWN_THRESHOLD:
        return "down"
    return "flat"


def _bucket_asymmetry(asymmetry_index: float) -> str:
    if asymmetry_index > ASYMMETRY_POS_THRESHOLD:
        return "pos"
    if asymmetry_index < ASYMMETRY_NEG_THRESHOLD:
        return "neg"
    return "neutral"


def compute_signal(
    composite_score: float,
    roc: float,
    asymmetry_index: float,
) -> str:
    """
    Map (composite_score, roc, asymmetry_index) → 5-state signal string.

    Returns one of: "strong_buy", "buy", "hold", "sell", "strong_sell".
    Raises: KeyError if the bucket combination is not in DECISION_MATRIX.
    Note: ROC thresholds use absolute values (not trend). Revisit post-backtesting.
    """
    key = (
        _bucket_score(composite_score),
        _bucket_momentum(roc),
        _bucket_asymmetry(asymmetry_index),
    )
    signal = DECISION_MATRIX.get(key)
    if signal is None:
        raise KeyError(
            f"No matrix entry for {key}. "
            f"Score bucket={key[0]}, Momentum={key[1]}, Asymmetry={key[2]}"
        )
    return signal


# ── Position sizing ───────────────────────────────────────────────────────────

def _lookup_range_table(
    value: float,
    table: list[tuple[float, float, float]],
    label: str,
) -> float:
    """Return the output for the first matching (low, high, output) range."""
    for low, high, output in table:
        if low <= value < high:
            return output
    raise ValueError(
        f"{label}={value} is outside all defined ranges. "
        f"Ranges: {[(lo, hi) for lo, hi, _ in table]}"
    )


def compute_position_size(
    signal: str,
    composite_score: float,
    volatility: float,
) -> dict[str, float]:
    """
    Compute 3-layer position size: Base × Conviction × Volatility.

    signal: one of the 5 signal strings.
    composite_score: used to determine conviction multiplier.
    volatility: stock beta (or equivalent volatility measure vs Nifty 50).

    Returns dict with keys:
        base_pct, conviction_multiplier, volatility_adjustment, final_pct
    """
    if signal not in POSITION_BASE_TABLE:
        raise ValueError(
            f"Unknown signal '{signal}'. "
            f"Expected one of: {sorted(POSITION_BASE_TABLE)}"
        )

    base_pct = POSITION_BASE_TABLE[signal]
    conviction = _lookup_range_table(
        composite_score, CONVICTION_MULTIPLIER_TABLE, "composite_score"
    )
    vol_adj = _lookup_range_table(
        volatility, VOLATILITY_ADJUSTMENT, "volatility"
    )
    final_pct = round(base_pct * conviction * vol_adj, 2)

    return {
        "base_pct": base_pct,
        "conviction_multiplier": conviction,
        "volatility_adjustment": vol_adj,
        "final_pct": final_pct,
    }


# ── Relative strength ─────────────────────────────────────────────────────────

def compute_relative_strength(
    stock_prices_6m: list[float],
    nifty_prices_6m: list[float],
) -> float:
    """
    Relative strength = stock_6m_return / nifty_6m_return.

    Returns 1.0 if nifty return is zero (guard against division by zero).
    Values > 1.0 mean the stock outperformed Nifty.
    """
    if len(stock_prices_6m) < 2 or len(nifty_prices_6m) < 2:
        raise ValueError("Price series must have at least 2 elements")

    stock_return = (stock_prices_6m[-1] - stock_prices_6m[0]) / stock_prices_6m[0]
    nifty_return = (nifty_prices_6m[-1] - nifty_prices_6m[0]) / nifty_prices_6m[0]

    if math.isclose(nifty_return, 0.0, abs_tol=1e-9):
        return 1.0  # neutral fallback when index is flat
    return stock_return / nifty_return


# ── Time Stop ─────────────────────────────────────────────────────────────────

def compute_time_stop(price_history: list[float]) -> int:
    """
    Count consecutive months (from most recent) with no meaningful price movement.

    price_history: monthly closing prices, oldest first, most recent last.
    A month counts as "no movement" when abs((current - prior) / prior)
    < MEANINGFUL_MOVEMENT_THRESHOLD (currently 5%).

    Returns 0 if the most recent month shows meaningful movement.
    Framework rule: ≥ 12–18 months → consider exit.
    """
    if len(price_history) < 2:
        return 0

    months = 0
    for i in range(len(price_history) - 1, 0, -1):
        current = price_history[i]
        prior = price_history[i - 1]
        if prior == 0:
            break
        change = abs((current - prior) / prior)
        if change < MEANINGFUL_MOVEMENT_THRESHOLD:
            months += 1
        else:
            break
    return months


# ── Factor breakdown builder ──────────────────────────────────────────────────

def build_factor_breakdown(
    factors: dict[str, float],
    roc: float,
    asymmetry_index: float,
    time_stop_months: int,
    position_breakdown: dict[str, float],
) -> dict:
    """
    Build the factor_breakdown dict that maps to the JSONB schema in score_snapshots.

    factors: dict keyed by factor name with pre-normalised values in [-1, +1].
    Returns a dict that validates against FactorBreakdown Pydantic model.
    """
    factors_list = [
        {
            "name": name,
            "weight": weight,
            "raw_value": factors[name],
            "weighted_contribution": round(factors[name] * weight, 6),
            "signal": "positive" if factors[name] >= 0 else "negative",
        }
        for name, weight in FACTOR_WEIGHTS.items()
    ]

    return {
        "factors": factors_list,
        "roc": roc,
        "asymmetry_index": asymmetry_index,
        "time_stop_months": time_stop_months,
        "position_breakdown": position_breakdown,
    }
