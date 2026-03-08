"""
Cloudflare R2 Storage helpers — fully async via aioboto3.

R2 is S3-compatible: we use aioboto3 with a custom endpoint.
Public objects are served via the R2 public development URL.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import aioboto3
from botocore.config import Config as BotoConfig

from app.config import settings

logger: logging.Logger = logging.getLogger(__name__)

BUCKET_NAME: str = settings.r2_bucket_name


@asynccontextmanager
async def _get_s3_client() -> AsyncGenerator[Any, None]:
    """Yield an async S3 client configured for Cloudflare R2."""
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
        config=BotoConfig(
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    ) as client:
        yield client


async def ensure_bucket() -> None:
    """Create the storage bucket if it does not already exist."""
    async with _get_s3_client() as client:
        try:
            await client.head_bucket(Bucket=BUCKET_NAME)
        except client.exceptions.ClientError:
            await client.create_bucket(Bucket=BUCKET_NAME)
            logger.info("Created R2 bucket: %s", BUCKET_NAME)


def resolve_storage_url(image_url: str) -> str:
    """Convert 'storage:path/to/file' to a public R2 URL.

    Unlike Supabase signed URLs, R2 public dev URLs are static and
    don't expire, so this is a synchronous string operation.
    """
    if not image_url or not image_url.startswith("storage:"):
        return image_url
    path: str = image_url.removeprefix("storage:")
    return f"{settings.r2_public_url}/{path}"


async def upload_file(
    storage_path: str,
    data: bytes,
    content_type: str,
) -> None:
    """Upload a file to Cloudflare R2."""
    async with _get_s3_client() as client:
        await client.put_object(
            Bucket=BUCKET_NAME,
            Key=storage_path,
            Body=data,
            ContentType=content_type,
            # Cache immutable assets for 1 year — safe because filenames
            # contain UUIDs (new content = new URL, no stale cache risk).
            CacheControl="public, max-age=31536000, immutable",
        )


async def remove_files(paths: list[str]) -> None:
    """Remove files from Cloudflare R2."""
    if not paths:
        return
    async with _get_s3_client() as client:
        objects: list[dict[str, str]] = [{"Key": p} for p in paths]
        await client.delete_objects(
            Bucket=BUCKET_NAME,
            Delete={"Objects": objects},
        )
