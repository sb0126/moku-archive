"""
Sentry SDK initialisation & helpers.

Initialise Sentry **once** at import time — before the FastAPI ``app``
object is created — so that the ASGI integration hooks into every request.

Usage:
    from app.sentry import init_sentry
    init_sentry()  # call from main.py top-level
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger: logging.Logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Bootstrap Sentry SDK if a DSN is configured.

    Safe to call even when ``SENTRY_DSN`` is empty — it simply no-ops.
    """
    if not settings.sentry_dsn:
        logger.info("ℹ️  SENTRY_DSN not set — Sentry is disabled")
        return

    try:
        import sentry_sdk  # type: ignore[import-untyped]
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore[import-untyped]
        from sentry_sdk.integrations.starlette import StarletteIntegration  # type: ignore[import-untyped]
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration  # type: ignore[import-untyped]
        from sentry_sdk.integrations.logging import LoggingIntegration  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("⚠️  sentry-sdk is not installed — skipping Sentry init")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=f"moku-api@0.1.0",
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        send_default_pii=False,  # GDPR-safe: no IP, cookies, etc.
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,       # breadcrumbs from INFO+
                event_level=logging.ERROR,  # only ERROR+ create events
            ),
        ],
        # Filter out expected HTTP errors (4xx) so they don't pollute Sentry
        before_send=_before_send,
    )
    logger.info(
        "✅ Sentry initialised (env=%s, traces=%.0f%%, profiles=%.0f%%)",
        settings.sentry_environment,
        settings.sentry_traces_sample_rate * 100,
        settings.sentry_profiles_sample_rate * 100,
    )


def _before_send(
    event: dict[str, Any],
    hint: dict[str, Any],
) -> dict[str, Any] | None:
    """Filter / enrich events before they are shipped to Sentry.

    - Suppress expected 4xx errors (DomainError, HTTPException with 4xx).
    - Add the request URL as a tag for easier search.
    """
    from fastapi import HTTPException

    from app.services.exceptions import DomainError

    exc_info = hint.get("exc_info")
    if exc_info:
        exc_value = exc_info[1] if len(exc_info) > 1 else None
        # Drop domain errors — these are expected validation/auth failures
        if isinstance(exc_value, DomainError):
            return None
        # Drop FastAPI HTTPExceptions with 4xx status codes
        if isinstance(exc_value, HTTPException):
            if 400 <= exc_value.status_code < 500:
                return None

    return event


def set_user_context(*, admin: bool = False, ip: str | None = None) -> None:
    """Attach lightweight user context to the current Sentry scope."""
    try:
        import sentry_sdk  # type: ignore[import-untyped]

        scope = sentry_sdk.get_current_scope()
        user_data: dict[str, Any] = {"role": "admin" if admin else "visitor"}
        if ip:
            user_data["ip_address"] = ip
        scope.set_user(user_data)
    except Exception:
        pass  # Sentry not available or not initialised


def capture_message(message: str, *, level: str = "info") -> None:
    """Send an arbitrary message to Sentry (for notable non-error events)."""
    try:
        import sentry_sdk  # type: ignore[import-untyped]

        sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


def add_breadcrumb(
    message: str,
    *,
    category: str = "app",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb to the current Sentry scope for debugging context."""
    try:
        import sentry_sdk  # type: ignore[import-untyped]

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {},
        )
    except Exception:
        pass
