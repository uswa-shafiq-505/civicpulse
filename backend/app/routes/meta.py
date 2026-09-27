from fastapi import APIRouter

from app.config import settings
from app.schemas import ProvidersOut
from app.services.triage_service import get_recent_triages

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/providers", response_model=ProvidersOut)
def providers():
    return ProvidersOut(
        active_provider=settings.TRIAGE_PROVIDER,
        recent_triages=get_recent_triages(),
    )
