"""
Admin router — /api/admin

HTTP layer only: login, stats, image upload/delete.
Delegates to admin_service, translates exceptions.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import require_admin
from app.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminStatsResponse,
    DeleteImageRequest,
    ImageUploadResponse,
    SuccessResponse,
)
from app.services import limiter
from app.services.exceptions import DomainError
from app.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── exception translator ──────────────────────────────────────


def _raise(exc: DomainError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


# ═══════════════════════════════════════════════════════════════
# POST /login  — admin login (rate-limited, return JWT)
# ═══════════════════════════════════════════════════════════════


@router.post("/login", response_model=AdminLoginResponse)
@limiter.limit("5/minute")
async def admin_login(
    request: Request,
    body: AdminLoginRequest,
) -> AdminLoginResponse:
    try:
        return await admin_service.login(body.password)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# GET /stats  — aggregate counts (admin)
# ═══════════════════════════════════════════════════════════════


@router.get("/stats", response_model=AdminStatsResponse)
@limiter.limit("30/minute")
async def get_stats(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> AdminStatsResponse:
    try:
        return await admin_service.get_stats(session)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /upload-image  — multipart upload (admin, 5MB limit)
# ═══════════════════════════════════════════════════════════════


@router.post("/upload-image", response_model=ImageUploadResponse)
@limiter.limit("10/minute")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    _admin: bool = Depends(require_admin),
) -> ImageUploadResponse:
    content_type: str = file.content_type or ""
    data: bytes = await file.read()
    try:
        return await admin_service.upload_image(data, content_type)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# POST /delete-image  — remove from storage (admin)
# ═══════════════════════════════════════════════════════════════


@router.post("/delete-image", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def delete_image(
    request: Request,
    body: DeleteImageRequest,
    _admin: bool = Depends(require_admin),
) -> SuccessResponse:
    try:
        return await admin_service.delete_image(body.path)
    except DomainError as exc:
        _raise(exc)
        raise
