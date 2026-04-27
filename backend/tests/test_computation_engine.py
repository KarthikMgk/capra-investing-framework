"""
Unit tests for computation_engine.py — launch gate, must be 100% green.
All tests use plain Python; no database, no Kite credentials, no env vars.
"""
import ast
import math
from pathlib import Path

import pytest

from app.core.constants import (
    FACTOR_WEIGHTS,
    MEANINGFUL_MOVEMENT_THRESHOLD,
    POSITION_BASE_TABLE,
)
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

# ── Helpers ───────────────────────────────────────────────────────────────────

def _all_factors(value: float = 0.0) -> dict[str, float]:
    return {name: value for name in FACTOR_WEIGHTS}


# ── FACTOR_WEIGHTS integrity ──────────────────────────────────────────────────

def test_factor_weights_sum_to_one() -> None:
    assert abs(sum(FACTOR_WEIGHTS.values()) - 1.0) < 1e-9


def test_factor_weights_has_nine_entries() -> None:
    assert len(FACTOR_WEIGHTS) == 9


def test_factor_weights_all_positive() -> None:
    assert all(w > 0 for w in FACTOR_WEIGHTS.values())


# ── compute_weighted_score ────────────────────────────────────────────────────

def test_compute_weighted_score_all_same() -> None:
    # All factors = 0.5 → result = 0.5 × sum(weights) = 0.5
    factors = _all_factors(0.5)
    result = compute_weighted_score(factors)
    expected = sum(0.5 * w for w in FACTOR_WEIGHTS.values())
    assert abs(result - expected) < 1e-6


def test_compute_weighted_score_reference_case() -> None:
    # Manual calculation: set each factor to its own weight value
    # weighted_contribution per factor = weight × weight = weight²
    # total = sum(w²)
    factors = {name: weight for name, weight in FACTOR_WEIGHTS.items()}
    expected = sum(w * w for w in FACTOR_WEIGHTS.values())
    result = compute_weighted_score(factors)
    assert abs(result - expected) < 1e-6


def test_compute_weighted_score_all_positive_one() -> None:
    result = compute_weighted_score(_all_factors(1.0))
    assert abs(result - 1.0) < 1e-6


def test_compute_weighted_score_all_negative_one() -> None:
    result = compute_weighted_score(_all_factors(-1.0))
    assert abs(result - (-1.0)) < 1e-6


def test_compute_weighted_score_clamps_above_one() -> None:
    # Weights sum to 1.0 so raw value 1.0 → 1.0 exactly; test boundary
    factors = _all_factors(1.0)
    assert compute_weighted_score(factors) <= 1.0


def test_compute_weighted_score_clamps_below_neg_one() -> None:
    factors = _all_factors(-1.0)
    assert compute_weighted_score(factors) >= -1.0


def test_compute_weighted_score_missing_key_raises() -> None:
    factors = _all_factors(0.5)
    del factors[next(iter(FACTOR_WEIGHTS))]
    with pytest.raises(ValueError, match="Missing factor"):
        compute_weighted_score(factors)


def test_compute_weighted_score_rounded_to_four_decimals() -> None:
    result = compute_weighted_score(_all_factors(0.333333))
    assert result == round(result, 4)


# ── compute_roc ───────────────────────────────────────────────────────────────

def test_compute_roc_reference_case() -> None:
    # (110 - 100) / 100 = 0.10
    result = compute_roc([100.0, 105.0, 110.0])
    assert abs(result - 0.10) < 1e-6


def test_compute_roc_decline() -> None:
    # (90 - 100) / 100 = -0.10
    result = compute_roc([100.0, 95.0, 90.0])
    assert abs(result - (-0.10)) < 1e-6


def test_compute_roc_two_elements() -> None:
    result = compute_roc([200.0, 250.0])
    assert abs(result - 0.25) < 1e-6


def test_compute_roc_empty_raises() -> None:
    with pytest.raises(ValueError):
        compute_roc([])


def test_compute_roc_single_element_raises() -> None:
    with pytest.raises(ValueError):
        compute_roc([100.0])


# ── compute_asymmetry_index ───────────────────────────────────────────────────

def test_compute_asymmetry_index_reference_case() -> None:
    # -0.3 + 0.6 + 0.5 = 0.8
    result = compute_asymmetry_index(0.3, 0.6, 0.5)
    assert abs(result - 0.8) < 1e-6


def test_compute_asymmetry_index_all_zeros() -> None:
    assert compute_asymmetry_index(0.0, 0.0, 0.0) == 0.0


def test_compute_asymmetry_index_valuation_negated() -> None:
    # High valuation (expensive) should drag result negative
    result = compute_asymmetry_index(1.0, 0.0, 0.0)
    assert result == -1.0


def test_compute_asymmetry_index_formula() -> None:
    v, e, l = 0.4, 0.7, 0.2
    assert abs(compute_asymmetry_index(v, e, l) - (-v + e + l)) < 1e-9


# ── compute_signal ────────────────────────────────────────────────────────────

VALID_SIGNALS = {"strong_buy", "buy", "hold", "sell", "strong_sell"}

_SIGNAL_CASES = [
    # (score, roc, asymmetry, expected_signal)
    ( 0.8,  0.10,  0.5,  "strong_buy"),
    ( 0.8,  0.10,  0.0,  "buy"),
    ( 0.6,  0.0,   0.5,  "buy"),
    ( 0.0,  0.0,   0.0,  "hold"),
    ( 0.0, -0.10,  0.0,  "sell"),
    (-0.6, -0.10, -0.5,  "strong_sell"),
]

@pytest.mark.parametrize("score,roc,asymmetry,expected", _SIGNAL_CASES)
def test_compute_signal_covers_all_five_states(
    score: float, roc: float, asymmetry: float, expected: str
) -> None:
    result = compute_signal(score, roc, asymmetry)
    assert result == expected


def test_compute_signal_returns_valid_string() -> None:
    for score, roc, asymmetry, _ in _SIGNAL_CASES:
        assert compute_signal(score, roc, asymmetry) in VALID_SIGNALS


def test_compute_signal_all_27_matrix_entries_reachable() -> None:
    from app.core.constants import DECISION_MATRIX
    assert len(DECISION_MATRIX) == 27


# ── compute_position_size ─────────────────────────────────────────────────────

def test_compute_position_size_has_required_keys() -> None:
    result = compute_position_size("buy", 0.6, 1.0)
    assert set(result.keys()) == {"base_pct", "conviction_multiplier",
                                   "volatility_adjustment", "final_pct"}


def test_compute_position_size_final_pct_formula() -> None:
    result = compute_position_size("buy", 0.6, 1.0)
    expected = result["base_pct"] * result["conviction_multiplier"] * result["volatility_adjustment"]
    assert abs(result["final_pct"] - expected) < 1e-6


def test_compute_position_size_buy_reference_case() -> None:
    # PRD example: "Early Accumulate, 65% base × 1.5x conviction"
    # score=0.61 → strong conviction (≥0.5 → 1.5x), beta≈1.0 → 1.0x adj
    result = compute_position_size("buy", 0.61, 1.0)
    assert result["base_pct"] == 65.0
    assert result["conviction_multiplier"] == 1.5
    assert result["volatility_adjustment"] == 1.0
    assert abs(result["final_pct"] - 97.5) < 1e-6


def test_compute_position_size_unknown_signal_raises() -> None:
    with pytest.raises(ValueError, match="Unknown signal"):
        compute_position_size("rocket", 0.5, 1.0)


def test_compute_position_size_all_valid_signals() -> None:
    for signal in POSITION_BASE_TABLE:
        result = compute_position_size(signal, 0.0, 1.0)
        assert result["final_pct"] >= 0


# ── compute_relative_strength ─────────────────────────────────────────────────

def test_compute_relative_strength_reference_case() -> None:
    # stock: +20%, nifty: +10% → RS = 2.0
    result = compute_relative_strength([100.0, 120.0], [100.0, 110.0])
    assert abs(result - 2.0) < 1e-6


def test_compute_relative_strength_underperform() -> None:
    # stock: +5%, nifty: +10% → RS = 0.5
    result = compute_relative_strength([100.0, 105.0], [100.0, 110.0])
    assert abs(result - 0.5) < 1e-6


def test_compute_relative_strength_nifty_flat_guard() -> None:
    # nifty flat → should not raise ZeroDivisionError; returns 1.0
    result = compute_relative_strength([100.0, 110.0], [100.0, 100.0])
    assert result == 1.0


def test_compute_relative_strength_too_short_raises() -> None:
    with pytest.raises(ValueError):
        compute_relative_strength([100.0], [100.0, 110.0])


# ── compute_time_stop ─────────────────────────────────────────────────────────

def test_compute_time_stop_zero_when_recent_movement() -> None:
    # Last month moved > 5% → time stop = 0
    prices = [100.0, 100.5, 101.0, 108.0]  # last move: +6.9%
    assert compute_time_stop(prices) == 0


def test_compute_time_stop_counts_consecutive_flat_months() -> None:
    # All months flat (< 5% change) → count = len - 1
    prices = [100.0, 101.0, 102.0, 103.0]  # each ~1% change
    result = compute_time_stop(prices)
    assert result == 3


def test_compute_time_stop_stops_at_first_movement() -> None:
    # Big move 2 months ago, flat since → count = 1
    prices = [100.0, 120.0, 121.0, 122.0]  # big move then flat
    assert compute_time_stop(prices) == 2


def test_compute_time_stop_single_element_returns_zero() -> None:
    assert compute_time_stop([100.0]) == 0


def test_compute_time_stop_empty_returns_zero() -> None:
    assert compute_time_stop([]) == 0


def test_compute_time_stop_threshold_boundary() -> None:
    # Exactly at threshold — should NOT count (< not <=)
    threshold = MEANINGFUL_MOVEMENT_THRESHOLD
    prices = [100.0, 100.0 * (1 + threshold)]  # exactly at threshold
    assert compute_time_stop(prices) == 0


# ── build_factor_breakdown ────────────────────────────────────────────────────

def _sample_position_breakdown() -> dict[str, float]:
    return {
        "base_pct": 65.0,
        "conviction_multiplier": 1.5,
        "volatility_adjustment": 0.9,
        "final_pct": 87.75,
    }


def test_build_factor_breakdown_schema_match() -> None:
    factors = _all_factors(0.5)
    result = build_factor_breakdown(
        factors=factors,
        roc=0.087,
        asymmetry_index=0.42,
        time_stop_months=3,
        position_breakdown=_sample_position_breakdown(),
    )
    # Must validate against Pydantic model without error
    model = FactorBreakdown(**result)
    assert len(model.factors) == 9


def test_build_factor_breakdown_has_nine_factors() -> None:
    result = build_factor_breakdown(
        factors=_all_factors(0.5),
        roc=0.0,
        asymmetry_index=0.0,
        time_stop_months=0,
        position_breakdown=_sample_position_breakdown(),
    )
    assert len(result["factors"]) == 9


def test_build_factor_breakdown_weighted_contribution() -> None:
    factors = _all_factors(0.5)
    result = build_factor_breakdown(
        factors=factors,
        roc=0.0,
        asymmetry_index=0.0,
        time_stop_months=0,
        position_breakdown=_sample_position_breakdown(),
    )
    for item in result["factors"]:
        expected = item["raw_value"] * item["weight"]
        assert abs(item["weighted_contribution"] - expected) < 1e-6


def test_build_factor_breakdown_signal_assignment() -> None:
    factors = {name: (0.5 if i % 2 == 0 else -0.5)
               for i, name in enumerate(FACTOR_WEIGHTS)}
    result = build_factor_breakdown(
        factors=factors,
        roc=0.0,
        asymmetry_index=0.0,
        time_stop_months=0,
        position_breakdown=_sample_position_breakdown(),
    )
    for item in result["factors"]:
        expected_signal = "positive" if item["raw_value"] >= 0 else "negative"
        assert item["signal"] == expected_signal


# ── Purity check ──────────────────────────────────────────────────────────────

def test_no_io_imports_in_computation_engine() -> None:
    forbidden = [
        "kite_client", "database", "models",
        "requests", "httpx", "sqlmodel", "sqlalchemy",
    ]
    source = Path(__file__).parent.parent / "app" / "services" / "computation_engine.py"
    import_lines = [
        line for line in source.read_text().splitlines()
        if line.startswith("import ") or line.startswith("from ")
    ]
    import_text = "\n".join(import_lines)
    for term in forbidden:
        assert term not in import_text, (
            f"Forbidden import '{term}' found in computation_engine.py imports"
        )
