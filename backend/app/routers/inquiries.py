"""
Inquiries router — /api/inquiries

HTTP layer only: delegate to inquiry_service, translate exceptions.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import require_admin
from app.schemas import (
    InquiryCreate,
    InquiryCreateResponse,
    InquiryListResponse,
    InquiryStatusUpdate,
    InquiryStatusUpdateResponse,
    SuccessResponse,
)
from app.services import limiter
from app.services.exceptions import DomainError
from app.services import inquiry_service

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])


# ── exception translator ──────────────────────────────────────


def _raise(exc: DomainError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


# ═══════════════════════════════════════════════════════════════
# POST /  — create inquiry (public)
# ═══════════════════════════════════════════════════════════════


@router.post("", response_model=InquiryCreateResponse, status_code=201)
@limiter.limit("3/minute")
async def create_inquiry(
    request: Request,
    body: InquiryCreate,
    session: AsyncSession = Depends(get_session),
) -> InquiryCreateResponse:
    try:
        return await inquiry_service.create_inquiry(session, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# GET /  — list all inquiries (admin)
# ═══════════════════════════════════════════════════════════════


@router.get("", response_model=InquiryListResponse)
@limiter.limit("30/minute")
async def list_inquiries(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> InquiryListResponse:
    try:
        return await inquiry_service.list_inquiries(session)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# PUT /{inquiry_id}/status  — update status + admin_note (admin)
# ═══════════════════════════════════════════════════════════════


@router.put("/{inquiry_id}/status", response_model=InquiryStatusUpdateResponse)
@limiter.limit("10/minute")
async def update_inquiry_status(
    request: Request,
    inquiry_id: str,
    body: InquiryStatusUpdate,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> InquiryStatusUpdateResponse:
    try:
        return await inquiry_service.update_inquiry_status(session, inquiry_id, body)
    except DomainError as exc:
        _raise(exc)
        raise


# ═══════════════════════════════════════════════════════════════
# DELETE /{inquiry_id}  — delete inquiry (admin)
# ═══════════════════════════════════════════════════════════════


@router.delete("/{inquiry_id}", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def delete_inquiry(
    request: Request,
    inquiry_id: str,
    session: AsyncSession = Depends(get_session),
    _admin: bool = Depends(require_admin),
) -> SuccessResponse:
    try:
        return await inquiry_service.delete_inquiry(session, inquiry_id)
    except DomainError as exc:
        _raise(exc)
        raise
