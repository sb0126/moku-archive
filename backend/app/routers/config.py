"""
Config router — /api

Public: return GA measurement ID and site verification codes.
"""

from fastapi import APIRouter, Request

from app.config import settings
from app.schemas import SiteConfigResponse, VerificationConfig
from app.services import limiter

router = APIRouter(prefix="/api", tags=["config"])


# ═══════════════════════════════════════════════════════════════
# GET /config  — public site configuration
# ═══════════════════════════════════════════════════════════════


@router.get("/config", response_model=SiteConfigResponse)
@limiter.limit("60/minute")
async def get_config(request: Request) -> SiteConfigResponse:
    return SiteConfigResponse(
        ga_measurement_id=settings.ga_measurement_id,
        verification=VerificationConfig(
            google=settings.google_site_verification or None,
            naver=settings.naver_site_verification or None,
        ),
    )
