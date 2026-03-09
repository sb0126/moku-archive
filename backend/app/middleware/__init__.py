"""Cache-Control header middleware.

Adds appropriate ``Cache-Control`` headers to GET responses based on the
request path.  This enables Vercel Edge CDN caching for public endpoints
(articles, config) while keeping private/realtime endpoints uncacheable.

Policy summary:
  - ``/api/articles``      → public, CDN 5 min, browser 1 min
  - ``/api/articles/{id}`` → public, CDN 10 min, browser 1 min
  - ``/api/config``        → public, CDN 1 day, browser 1 hour
  - ``/api/health|ready``  → no-cache, no-store
  - ``/api/posts|comments|inquiries|admin`` → private, no-cache
"""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


# Exact-path → Cache-Control mapping
_EXACT_POLICIES: dict[str, str] = {
    "/api/articles": "public, max-age=60, s-maxage=300, stale-while-revalidate=60",
    "/api/config": "public, max-age=3600, s-maxage=86400",
    "/api/health": "no-cache, no-store",
    "/api/ready": "no-cache, no-store",
}

# Prefixes for private/no-cache routes
_PRIVATE_PREFIXES: tuple[str, ...] = (
    "/api/posts",
    "/api/comments",
    "/api/inquiries",
    "/api/admin",
)


class CacheHeaderMiddleware(BaseHTTPMiddleware):
    """Inject Cache-Control headers on GET responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response: Response = await call_next(request)

        # Only cache GET responses with 2xx status
        if request.method != "GET" or response.status_code >= 300:
            return response

        path = request.url.path

        # 1. Exact-path lookup
        policy = _EXACT_POLICIES.get(path)
        if policy is not None:
            response.headers["Cache-Control"] = policy
            return response

        # 2. Article detail: /api/articles/{id}  (exactly 3 slashes)
        if path.startswith("/api/articles/") and path.count("/") == 3:
            response.headers["Cache-Control"] = (
                "public, max-age=60, s-maxage=600, stale-while-revalidate=120"
            )
            return response

        # 3. Private routes (posts, comments, inquiries, admin)
        if any(path.startswith(prefix) for prefix in _PRIVATE_PREFIXES):
            response.headers["Cache-Control"] = "private, no-cache"
            return response

        return response
