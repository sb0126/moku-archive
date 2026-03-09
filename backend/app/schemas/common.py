from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model that serialises fields as camelCase JSON.

    All *Response* schemas should inherit from this so the frontend
    (which expects camelCase) receives the correct field names without
    needing manual aliases everywhere.
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,  # also accept snake_case in tests / internal code
    }


class SuccessResponse(CamelModel):
    success: bool = True
    message: str


class ErrorResponse(CamelModel):
    error: str
    details: str | None = None


# ── Health / Readiness probes ─────────────────────────────────


class HealthResponse(CamelModel):
    """Liveness probe response."""

    status: str


class ReadinessResponse(CamelModel):
    """Readiness probe response (includes DB connectivity)."""

    status: str
    db: str
