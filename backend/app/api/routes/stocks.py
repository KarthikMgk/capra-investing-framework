from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.constants import NIFTY_50_NAMES, NIFTY_50_SYMBOLS
from app.models.score_snapshot import ScoreSnapshot
from app.schemas.stock import (
    FactorBreakdown,
    StockListItem,
    StockListResponse,
    StockScoreResponse,
)

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=StockListResponse)
def list_stocks(session: SessionDep, _: CurrentUser) -> StockListResponse:
    """Return all 50 Nifty 50 stocks with their latest signal (null if not yet computed)."""
    signal_map: dict[str, str] = {}
    for row in session.exec(
        select(ScoreSnapshot.stock_symbol, ScoreSnapshot.signal)
        .order_by(ScoreSnapshot.computation_timestamp.desc())  # type: ignore[attr-defined]
    ):
        sym, sig = row
        if sym not in signal_map:
            signal_map[sym] = sig
        if len(signal_map) == len(NIFTY_50_SYMBOLS):
            break

    items = [
        StockListItem(
            stock_symbol=sym,
            name=NIFTY_50_NAMES.get(sym, sym),
            signal=signal_map.get(sym),
        )
        for sym in NIFTY_50_SYMBOLS
    ]
    return StockListResponse(items=items, total=len(items))


@router.get("/{stock_symbol}", response_model=StockScoreResponse)
def get_stock(stock_symbol: str, session: SessionDep, _: CurrentUser) -> StockScoreResponse:
    """Return the latest score snapshot for a stock. No live Kite call — cache only."""
    snapshot = session.exec(
        select(ScoreSnapshot)
        .where(ScoreSnapshot.stock_symbol == stock_symbol.upper())
        .order_by(ScoreSnapshot.computation_timestamp.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()

    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SCORE_NOT_FOUND",
                    "message": f"No score computed for {stock_symbol}. Run a data refresh first.",
                }
            },
        )

    return StockScoreResponse(
        stock_symbol=snapshot.stock_symbol,
        composite_score=snapshot.composite_score,
        signal=snapshot.signal,
        position_size=snapshot.position_size,
        computation_timestamp=snapshot.computation_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        kite_snapshot_ts=snapshot.kite_snapshot_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        screener_csv_ts=snapshot.screener_csv_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        rbi_csv_ts=snapshot.rbi_csv_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        factor_breakdown=FactorBreakdown(**snapshot.factor_breakdown),
    )
