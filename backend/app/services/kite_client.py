"""
Kite Connect client — all Kite API communication goes through this class.
Never import kiteconnect outside this file. Never call raw HTTP here either.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from datetime import datetime as dt
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from kiteconnect import KiteConnect
from sqlmodel import Session, select

from app.core.encryption import decrypt
from app.core.exceptions import KiteAPIError
from app.models.kite_settings import KiteSettings
from app.schemas.portfolio import HoldingData, QuoteData

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

# Module-level instrument token cache — populated on first use, shared across instances
_instrument_cache: dict[str, int] = {}


class KiteClient:
    def __init__(self, session: Session) -> None:
        row = session.exec(select(KiteSettings)).first()
        if not row:
            raise KiteAPIError("No Kite credentials found — upload them via /admin/settings")

        api_key = decrypt(row.api_key_encrypted)
        access_token = decrypt(row.access_token_encrypted)

        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

        logger.info("KiteClient initialised for API key ending in ...%s", api_key[-4:])

    # ── Holdings ─────────────────────────────────────────────────────────────

    def get_holdings(self) -> list[HoldingData]:
        try:
            raw = self.kite.holdings()
            return [self._parse_holding(item) for item in raw]
        except KiteAPIError:
            raise
        except Exception as e:
            logger.error("KiteClient.get_holdings failed: %s", e, exc_info=True)
            raise KiteAPIError(f"Failed to fetch holdings: {e}") from e

    def _parse_holding(self, item: dict) -> HoldingData:
        self._validate_holding_item(item)
        return HoldingData(
            tradingsymbol=item["tradingsymbol"],
            quantity=float(item["quantity"]),
            last_price=float(item["last_price"]),
        )

    def _validate_holding_item(self, item: dict) -> None:
        required = {"tradingsymbol", "quantity", "last_price"}
        missing = required - item.keys()
        if missing:
            raise KiteAPIError(f"Holding response missing required fields: {missing}")

    # ── Quotes ───────────────────────────────────────────────────────────────

    def get_quote(self, symbols: list[str]) -> dict[str, QuoteData]:
        try:
            nse_symbols = [f"NSE:{s}" if ":" not in s else s for s in symbols]
            raw = self.kite.quote(nse_symbols)
            result: dict[str, QuoteData] = {}
            for key, data in raw.items():
                if "last_price" not in data:
                    raise KiteAPIError(f"Quote for {key} missing last_price")
                symbol = key.split(":")[-1]
                result[symbol] = QuoteData(
                    last_price=float(data["last_price"]),
                    change=float(data.get("change", 0.0)),
                    change_percent=float(data.get("change_percent", 0.0)),
                )
            return result
        except KiteAPIError:
            raise
        except Exception as e:
            logger.error("KiteClient.get_quote failed: %s", e, exc_info=True)
            raise KiteAPIError(f"Failed to fetch quotes: {e}") from e

    # ── Historical prices ─────────────────────────────────────────────────────

    def get_historical_prices(self, symbol: str, days: int) -> list[float]:
        try:
            token = self._get_instrument_token(symbol)
            to_date = dt.now(tz=IST).date()
            from_date = to_date - timedelta(days=days)
            raw = self.kite.historical_data(token, from_date, to_date, "day")
            if not raw:
                raise KiteAPIError(f"No historical data returned for {symbol}")
            for candle in raw:
                if "close" not in candle:
                    raise KiteAPIError(f"Historical candle missing 'close' for {symbol}")
            return [float(candle["close"]) for candle in raw]
        except KiteAPIError:
            raise
        except Exception as e:
            logger.error("KiteClient.get_historical_prices failed for %s: %s", symbol, e, exc_info=True)
            raise KiteAPIError(f"Failed to fetch historical prices for {symbol}: {e}") from e

    def get_nifty_index_prices(self, days: int) -> list[float]:
        try:
            token = self._get_instrument_token("NIFTY 50", segment="INDICES")
            to_date = dt.now(tz=IST).date()
            from_date = to_date - timedelta(days=days)
            raw = self.kite.historical_data(token, from_date, to_date, "day")
            if not raw:
                raise KiteAPIError("No Nifty 50 historical data returned")
            return [float(candle["close"]) for candle in raw]
        except KiteAPIError:
            raise
        except Exception as e:
            logger.error("KiteClient.get_nifty_index_prices failed: %s", e, exc_info=True)
            raise KiteAPIError(f"Failed to fetch Nifty 50 index prices: {e}") from e

    # ── Instrument token lookup ───────────────────────────────────────────────

    def _get_instrument_token(self, symbol: str, segment: str = "NSE") -> int:
        global _instrument_cache
        cache_key = f"{segment}:{symbol}"
        if cache_key in _instrument_cache:
            return _instrument_cache[cache_key]

        instruments = self.kite.instruments("NSE")
        for inst in instruments:
            seg = inst.get("segment", "")
            ts = inst.get("tradingsymbol", "")
            if ts == symbol and (segment == "NSE" or seg == segment):
                token = int(inst["instrument_token"])
                _instrument_cache[cache_key] = token
                return token

        raise KiteAPIError(f"Instrument token not found for {symbol} in segment {segment}")
