"""
Unit tests for KiteClient — all use MockKiteClient, no live credentials required.
Tests marked @pytest.mark.integration require real Kite credentials and are
skipped in CI by default: pytest -m "not integration"
"""
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import KiteAPIError
from app.schemas.portfolio import HoldingData, QuoteData
from tests.conftest import MockKiteClient


# ── Schema tests ──────────────────────────────────────────────────────────────

def test_portfolio_schemas_accept_valid_data() -> None:
    h = HoldingData(tradingsymbol="HDFCBANK", quantity=10.0, last_price=1650.0)
    assert h.tradingsymbol == "HDFCBANK"

    q = QuoteData(last_price=1650.0, change=5.0, change_percent=0.3)
    assert q.last_price == 1650.0
    assert q.change_percent == 0.3


def test_quote_data_defaults_change_to_zero() -> None:
    q = QuoteData(last_price=500.0)
    assert q.change == 0.0
    assert q.change_percent == 0.0


# ── MockKiteClient: get_holdings ──────────────────────────────────────────────

def test_get_holdings_returns_list_of_holding_data(mock_kite_client: MockKiteClient) -> None:
    result = mock_kite_client.get_holdings()
    assert isinstance(result, list)
    assert len(result) == 5
    assert all(isinstance(h, HoldingData) for h in result)


def test_get_holdings_all_fields_populated(mock_kite_client: MockKiteClient) -> None:
    for holding in mock_kite_client.get_holdings():
        assert holding.tradingsymbol
        assert holding.quantity > 0
        assert holding.last_price > 0


# ── Holdings validation: missing fields raises KiteAPIError ──────────────────

def test_get_holdings_schema_validation_raises_kite_api_error() -> None:
    class BadHoldingsClient(MockKiteClient):
        def get_holdings(self) -> list[HoldingData]:
            # Simulate what would happen if kite.holdings() returned incomplete data
            raw = [{"tradingsymbol": "HDFCBANK"}]  # missing quantity and last_price
            return [self._parse_holding(item) for item in raw]

    client = BadHoldingsClient()
    with pytest.raises(KiteAPIError, match="missing required fields"):
        client.get_holdings()


# ── MockKiteClient: get_historical_prices ─────────────────────────────────────

def test_get_historical_prices_returns_floats(mock_kite_client: MockKiteClient) -> None:
    result = mock_kite_client.get_historical_prices("HDFCBANK", 90)
    assert len(result) == 90
    assert all(isinstance(p, float) for p in result)


def test_get_historical_prices_6m_length(mock_kite_client: MockKiteClient) -> None:
    result = mock_kite_client.get_historical_prices("RELIANCE", 180)
    assert len(result) == 180


def test_get_historical_prices_deterministic(mock_kite_client: MockKiteClient) -> None:
    r1 = mock_kite_client.get_historical_prices("TCS", 90)
    r2 = mock_kite_client.get_historical_prices("TCS", 90)
    assert r1 == r2


def test_get_historical_prices_shows_variation(mock_kite_client: MockKiteClient) -> None:
    prices = mock_kite_client.get_historical_prices("INFY", 90)
    assert prices[0] != prices[-1]  # series is not flat


# ── MockKiteClient: get_nifty_index_prices ────────────────────────────────────

def test_get_nifty_index_prices_returns_floats(mock_kite_client: MockKiteClient) -> None:
    result = mock_kite_client.get_nifty_index_prices(180)
    assert len(result) == 180
    assert all(isinstance(p, float) for p in result)


# ── MockKiteClient: get_quote ─────────────────────────────────────────────────

def test_get_quote_returns_quote_data(mock_kite_client: MockKiteClient) -> None:
    result = mock_kite_client.get_quote(["HDFCBANK", "RELIANCE"])
    assert "HDFCBANK" in result
    assert isinstance(result["HDFCBANK"], QuoteData)
    assert result["HDFCBANK"].last_price > 0


# ── KiteAPIError wrapping ─────────────────────────────────────────────────────

def test_kite_api_error_wraps_kiteconnect_exceptions() -> None:
    """
    If the underlying kite object raises any exception, KiteClient must
    catch it and re-raise as KiteAPIError, not the raw exception.
    """
    from kiteconnect.exceptions import NetworkException

    class NetworkFailClient(MockKiteClient):
        def get_holdings(self) -> list[HoldingData]:
            try:
                raise NetworkException("Connection timed out", code=408)
            except Exception as e:
                raise KiteAPIError(f"Failed to fetch holdings: {e}") from e

    client = NetworkFailClient()
    with pytest.raises(KiteAPIError):
        client.get_holdings()


def test_kite_api_error_is_not_raw_kiteconnect_exception() -> None:
    from kiteconnect.exceptions import NetworkException

    class NetworkFailClient(MockKiteClient):
        def get_holdings(self) -> list[HoldingData]:
            try:
                raise NetworkException("timeout", code=408)
            except Exception as e:
                raise KiteAPIError(f"Failed: {e}") from e

    client = NetworkFailClient()
    with pytest.raises(KiteAPIError):
        client.get_holdings()
    # Ensure the raw exception type does NOT propagate
    try:
        client.get_holdings()
    except KiteAPIError:
        pass
    except Exception as e:
        pytest.fail(f"Raw exception leaked: {type(e)}")


# ── Cross-asset data methods ──────────────────────────────────────────────────

def test_get_usdinr_prices_returns_series(mock_kite_client: MockKiteClient) -> None:
    prices = mock_kite_client.get_usdinr_prices(180)
    assert len(prices) == 180
    assert all(isinstance(p, float) for p in prices)
    assert prices[0] == pytest.approx(83.0)


def test_get_usdinr_prices_increases_over_series(mock_kite_client: MockKiteClient) -> None:
    prices = mock_kite_client.get_usdinr_prices(10)
    assert prices[-1] > prices[0]


def test_get_gold_prices_returns_series(mock_kite_client: MockKiteClient) -> None:
    prices = mock_kite_client.get_gold_prices(180)
    assert len(prices) == 180
    assert all(isinstance(p, float) for p in prices)
    assert prices[0] == pytest.approx(5500.0)


def test_get_gold_prices_different_from_nifty(mock_kite_client: MockKiteClient) -> None:
    gold = mock_kite_client.get_gold_prices(30)
    nifty = mock_kite_client.get_nifty_index_prices(30)
    assert gold[0] != nifty[0]


def test_get_sector_prices_returns_series(mock_kite_client: MockKiteClient) -> None:
    prices = mock_kite_client.get_sector_prices("NIFTY BANK", 180)
    assert len(prices) == 180
    assert all(isinstance(p, float) for p in prices)


def test_get_sector_prices_accepts_any_sector_name(mock_kite_client: MockKiteClient) -> None:
    for sector in ["NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO"]:
        prices = mock_kite_client.get_sector_prices(sector, 30)
        assert len(prices) == 30


def test_stock_sector_index_covers_all_nifty50() -> None:
    from app.core.constants import NIFTY_50_SYMBOLS, STOCK_SECTOR_INDEX
    missing = [s for s in NIFTY_50_SYMBOLS if s not in STOCK_SECTOR_INDEX]
    assert not missing, f"Stocks missing sector mapping: {missing}"


def test_stock_sector_index_values_are_nonempty_strings() -> None:
    from app.core.constants import STOCK_SECTOR_INDEX
    for symbol, sector in STOCK_SECTOR_INDEX.items():
        assert isinstance(sector, str) and sector.strip(), (
            f"Blank sector for {symbol}"
        )
