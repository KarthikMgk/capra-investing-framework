"""
Tests for the in-memory CSV validator service (AC: 3, 4, 7, 10).
All tests pass bytes directly — no file paths, no open() calls.
"""
import io
import time

import pandas as pd
import pytest

from app.services.csv_validator import (
    RBI_REQUIRED_COLUMNS,
    SCREENER_REQUIRED_COLUMNS,
    validate_rbi,
    validate_screener,
)


def _screener_csv(**overrides: list) -> bytes:
    data = {col: overrides.get(col, ["TEST"] if col in ("Symbol", "Name") else [1.0])
            for col in SCREENER_REQUIRED_COLUMNS}
    return pd.DataFrame(data).to_csv(index=False).encode()


def _rbi_csv(**overrides: list) -> bytes:
    data = {
        "Date": ["2024-01-01"],
        "Repo_Rate": [6.5],
        "Credit_Growth": [12.3],
        "Liquidity_Indicator": [0.8],
    }
    data.update(overrides)
    return pd.DataFrame(data).to_csv(index=False).encode()


# ── validate_screener ──────────────────────────────────────────────────────

def test_screener_valid_csv_passes() -> None:
    result = validate_screener(_screener_csv())
    assert result.is_valid is True
    assert result.missing_columns == []


def test_screener_missing_pe_column_fails() -> None:
    df = pd.DataFrame({col: [1.0] for col in SCREENER_REQUIRED_COLUMNS if col != "PE"})
    df["Symbol"] = ["TEST"]
    df["Name"] = ["Test Corp"]
    csv_bytes = df.to_csv(index=False).encode()

    result = validate_screener(csv_bytes)

    assert result.is_valid is False
    assert "PE" in result.missing_columns


def test_screener_multiple_missing_columns() -> None:
    csv_bytes = b"Symbol,Name\nTEST,Test Corp\n"
    result = validate_screener(csv_bytes)
    assert result.is_valid is False
    assert len(result.missing_columns) > 0
    for missing in result.missing_columns:
        assert missing not in ["Symbol", "Name"]


def test_screener_empty_bytes_fails() -> None:
    result = validate_screener(b"")
    assert result.is_valid is False
    assert result.found_columns == []


def test_screener_found_columns_returned() -> None:
    csv_bytes = b"Symbol,Name\nTEST,Test Corp\n"
    result = validate_screener(csv_bytes)
    assert "Symbol" in result.found_columns
    assert "Name" in result.found_columns


# ── validate_rbi ──────────────────────────────────────────────────────────

def test_rbi_valid_csv_passes() -> None:
    result = validate_rbi(_rbi_csv())
    assert result.is_valid is True
    assert result.missing_columns == []


def test_rbi_missing_repo_rate_fails() -> None:
    csv_bytes = b"Date,Credit_Growth,Liquidity_Indicator\n2024-01-01,12.3,0.8\n"
    result = validate_rbi(csv_bytes)
    assert result.is_valid is False
    assert "Repo_Rate" in result.missing_columns


def test_rbi_empty_bytes_fails() -> None:
    result = validate_rbi(b"")
    assert result.is_valid is False


# ── performance (AC10) ────────────────────────────────────────────────────

def test_screener_validates_5000_rows_under_500ms() -> None:
    rows = 5000
    buf = io.StringIO()
    buf.write(",".join(SCREENER_REQUIRED_COLUMNS) + "\n")
    row = ",".join(
        "TEST" if col in ("Symbol", "Name") else "1.0"
        for col in SCREENER_REQUIRED_COLUMNS
    )
    for _ in range(rows):
        buf.write(row + "\n")
    csv_bytes = buf.getvalue().encode()

    start = time.perf_counter()
    result = validate_screener(csv_bytes)
    elapsed = time.perf_counter() - start

    assert result.is_valid is True
    assert elapsed < 0.5, f"Validation took {elapsed:.3f}s — exceeds 500ms budget"
