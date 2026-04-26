import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.api.deps import SessionDep, require_admin
from app.core.encryption import encrypt
from app.models.kite_settings import KiteSettings
from app.schemas.settings import KiteCredentialsStatus, KiteCredentialsUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get(
    "/kite",
    response_model=KiteCredentialsStatus,
    dependencies=[Depends(require_admin)],
)
def get_kite_settings(session: SessionDep) -> Any:
    row = session.exec(select(KiteSettings)).first()
    if not row:
        return KiteCredentialsStatus(
            api_key_set=False, access_token_set=False, updated_at=None
        )
    return KiteCredentialsStatus(
        api_key_set=bool(row.api_key_encrypted),
        access_token_set=bool(row.access_token_encrypted),
        updated_at=row.updated_at,
    )


@router.put("/kite", dependencies=[Depends(require_admin)])
def update_kite_settings(body: KiteCredentialsUpdate, session: SessionDep) -> Any:
    row = session.exec(select(KiteSettings)).first()
    if row:
        row.api_key_encrypted = encrypt(body.api_key)
        row.access_token_encrypted = encrypt(body.access_token)
        row.updated_at = datetime.now(timezone.utc)
        session.add(row)
    else:
        session.add(
            KiteSettings(
                api_key_encrypted=encrypt(body.api_key),
                access_token_encrypted=encrypt(body.access_token),
            )
        )
    session.commit()
    logger.info("kite credentials updated")
    return {"status": "ok"}
