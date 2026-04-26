from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import User
from app.schemas.portfolio import HoldingData, QuoteData
from app.services.kite_client import KiteClient
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        session.exec(delete(User))
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


# ── Kite mock ────────────────────────────────────────────────────────────────

_MOCK_SYMBOLS = ["HDFCBANK", "RELIANCE", "TCS", "INFY", "ICICIBANK"]

_MOCK_HOLDINGS: list[HoldingData] = [
    HoldingData(tradingsymbol=sym, quantity=10.0, last_price=1000.0 + i * 100)
    for i, sym in enumerate(_MOCK_SYMBOLS)
]

_MOCK_QUOTES: dict[str, QuoteData] = {
    sym: QuoteData(last_price=1000.0 + i * 100, change=5.0, change_percent=0.5)
    for i, sym in enumerate(_MOCK_SYMBOLS)
}


class MockKiteClient(KiteClient):
    def __init__(self, session: object = None) -> None:  # type: ignore[override]
        # Intentionally bypass parent __init__ — no DB or credential access
        self.kite = None  # type: ignore[assignment]

    def get_holdings(self) -> list[HoldingData]:
        return list(_MOCK_HOLDINGS)

    def get_quote(self, symbols: list[str]) -> dict[str, QuoteData]:
        return {s: _MOCK_QUOTES[s] for s in symbols if s in _MOCK_QUOTES}

    def get_historical_prices(self, symbol: str, days: int) -> list[float]:
        # Deterministic synthetic series: 100.0, 100.1, 100.2, ...
        return [100.0 + 0.1 * i for i in range(days)]

    def get_nifty_index_prices(self, days: int) -> list[float]:
        return [18000.0 + 10.0 * i for i in range(days)]


@pytest.fixture
def mock_kite_client() -> MockKiteClient:
    return MockKiteClient(session=None)
