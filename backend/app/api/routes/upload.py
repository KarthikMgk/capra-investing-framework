import io
import uuid
from datetime import date as DateType
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile

from app.api.deps import SessionDep, require_admin
from app.core.exceptions import CSVValidationError
from app.models.rbi_macro_data import RBIMacroData
from app.models.screener_data import ScreenerData
from app.schemas.upload import UploadResponse
from app.services.csv_validator import (
    RBI_REQUIRED_COLUMNS,
    SCREENER_REQUIRED_COLUMNS,
    validate_rbi,
    validate_screener,
)

router = APIRouter(prefix="/upload", tags=["upload"])


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if pd.notna(value) else None
    except (TypeError, ValueError):
        return None


def _safe_date(value: Any) -> DateType | None:
    try:
        return pd.to_datetime(value).date() if pd.notna(value) else None
    except Exception:
        return None


@router.post("/screener", response_model=UploadResponse, status_code=201)
async def upload_screener(
    file: UploadFile,
    session: SessionDep,
    _: Any = Depends(require_admin),
) -> Any:
    file_bytes = await file.read()
    result = validate_screener(file_bytes)
    if not result.is_valid:
        raise CSVValidationError(
            message="Required columns are missing from the uploaded CSV.",
            details={"expected": SCREENER_REQUIRED_COLUMNS, "found": result.found_columns},
        )

    batch_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    df = pd.read_csv(io.BytesIO(file_bytes))

    rows = [
        ScreenerData(
            upload_batch_id=batch_id,
            uploaded_at=now,
            symbol=str(row["Symbol"]),
            name=str(row["Name"]) if pd.notna(row.get("Name")) else None,
            pe=_safe_float(row.get("PE")),
            pb=_safe_float(row.get("PB")),
            eps=_safe_float(row.get("EPS")),
            roe=_safe_float(row.get("ROE")),
            debt_to_equity=_safe_float(row.get("Debt_to_Equity")),
            revenue_growth=_safe_float(row.get("Revenue_Growth")),
            promoter_holding=_safe_float(row.get("Promoter_Holding")),
        )
        for _, row in df.iterrows()
    ]
    session.add_all(rows)
    session.commit()

    return UploadResponse(batch_id=str(batch_id))


@router.post("/rbi", response_model=UploadResponse, status_code=201)
async def upload_rbi(
    file: UploadFile,
    session: SessionDep,
    _: Any = Depends(require_admin),
) -> Any:
    file_bytes = await file.read()
    result = validate_rbi(file_bytes)
    if not result.is_valid:
        raise CSVValidationError(
            message="Required columns are missing from the uploaded CSV.",
            details={"expected": RBI_REQUIRED_COLUMNS, "found": result.found_columns},
        )

    batch_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    df = pd.read_csv(io.BytesIO(file_bytes))

    rows = [
        RBIMacroData(
            upload_batch_id=batch_id,
            uploaded_at=now,
            date=_safe_date(row.get("Date")),
            repo_rate=_safe_float(row.get("Repo_Rate")),
            credit_growth=_safe_float(row.get("Credit_Growth")),
            liquidity_indicator=_safe_float(row.get("Liquidity_Indicator")),
        )
        for _, row in df.iterrows()
    ]
    session.add_all(rows)
    session.commit()

    return UploadResponse(batch_id=str(batch_id))
