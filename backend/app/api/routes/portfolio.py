from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models.score_snapshot import ScoreSnapshot
from app.schemas.portfolio import HoldingWithSignal, PortfolioResponse
from app.services.kite_client import KiteClient

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

_SIGNAL_COLOR: dict[str, str] = {
    "strong_buy": "emerald",
    "buy": "teal",
    "hold": "zinc",
    "sell": "amber",
    "strong_sell": "red",
}


@router.get("", response_model=PortfolioResponse)
def get_portfolio(session: SessionDep, _current_user: CurrentUser) -> PortfolioResponse:
    client = KiteClient(session)
    holdings = client.get_holdings()

    items: list[HoldingWithSignal] = []
    for holding in holdings:
        snapshot = session.exec(
            select(ScoreSnapshot)
            .where(ScoreSnapshot.stock_symbol == holding.tradingsymbol)
            .order_by(ScoreSnapshot.computation_timestamp.desc())
            .limit(1)
        ).first()

        signal = snapshot.signal if snapshot else None

        items.append(
            HoldingWithSignal(
                tradingsymbol=holding.tradingsymbol,
                name=holding.tradingsymbol,
                quantity=holding.quantity,
                last_price=holding.last_price,
                signal=signal,
                signal_color=_SIGNAL_COLOR.get(signal) if signal else None,
            )
        )

    return PortfolioResponse(items=items, total=len(items))
