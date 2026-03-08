from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    password: str = Field(min_length=1)


class AdminLoginResponse(BaseModel):
    success: bool = True
    authenticated: bool = True
    token: str


class AdminStats(BaseModel):
    total_inquiries: int
    pending_inquiries: int
    contacted_inquiries: int
    completed_inquiries: int
    total_posts: int
    total_views: int
    total_comments: int


class AdminStatsResponse(BaseModel):
    success: bool = True
    stats: AdminStats


class ImageUploadResponse(BaseModel):
    success: bool = True
    message: str
    url: str
    path: str


class DeleteImageRequest(BaseModel):
    """Typed request body for image deletion — prevents dict[str, str] anti-pattern."""
    path: str = Field(min_length=1)
