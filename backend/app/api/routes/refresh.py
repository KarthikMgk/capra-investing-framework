from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, get_kite_client, require_admin
from app.core.exceptions import ComputationError, KiteAPIError
from app.services import score_service
from app.services.kite_client import KiteClient

router = APIRouter(prefix="/refresh", tags=["refresh"])

KiteClientDep = Annotated[KiteClient, Depends(get_kite_client)]


@router.post("")
async def trigger_refresh(
    _current_user: Annotated[object, Depends(require_admin)],
    session: SessionDep,
    kite_client: KiteClientDep,
) -> dict:
    try:
        result = await score_service.run_full_refresh(
            session=session,
            kite_client=kite_client,
        )
        return {
            "status": "ok",
            "stocks_computed": result.stocks_computed,
            "computation_timestamp": result.computation_timestamp,
        }
    except KiteAPIError as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=502,
            detail={"error": {"code": "KITE_API_ERROR", "message": exc.message, "details": exc.details}},
        ) from exc
    except ComputationError as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "COMPUTATION_ERROR", "message": exc.message, "details": exc.details}},
        ) from exc
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "REFRESH_FAILED", "message": str(exc)}},
        ) from exc
