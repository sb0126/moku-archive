from pydantic import Field

from app.schemas.common import CamelModel


class AdminLoginRequest(CamelModel):
    password: str = Field(min_length=1)


class AdminLoginResponse(CamelModel):
    success: bool = True
    authenticated: bool = True
    token: str


class AdminStats(CamelModel):
    total_inquiries: int
    pending_inquiries: int
    contacted_inquiries: int
    completed_inquiries: int
    total_posts: int
    total_views: int
    total_comments: int


class AdminStatsResponse(CamelModel):
    success: bool = True
    stats: AdminStats


class ImageUploadResponse(CamelModel):
    success: bool = True
    message: str
    url: str
    path: str


class DeleteImageRequest(CamelModel):
    """Typed request body for image deletion — prevents dict[str, str] anti-pattern."""
    path: str = Field(min_length=1)

