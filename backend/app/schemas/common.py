from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    error: str
    details: str | None = None


# ── Health / Readiness probes ─────────────────────────────────


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str


class ReadinessResponse(BaseModel):
    """Readiness probe response (includes DB connectivity)."""

    status: str
    db: str
