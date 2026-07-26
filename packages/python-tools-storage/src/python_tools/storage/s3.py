"""S3 / MinIO client helpers (PT-11 T11.1)."""

from __future__ import annotations

from typing import Any

from python_tools.storage.keys import safe_key


def create_s3_client(
    *,
    endpoint_url: str | None = None,
    region_name: str = "us-east-1",
    access_key: str | None = None,
    secret_key: str | None = None,
) -> Any:
    """Build a boto3 S3 client. ``endpoint_url`` enables MinIO / path-style locals."""
    try:
        import boto3  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "boto3 is required for create_s3_client. Install python-tools-storage[s3]."
        ) from exc

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url or None,
        region_name=region_name,
        aws_access_key_id=access_key or None,
        aws_secret_access_key=secret_key or None,
    )


def ensure_bucket(client: Any | None, bucket: str) -> None:
    """Create ``bucket`` if missing (no-op when ``client`` is None)."""
    if client is None:
        return
    try:
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "botocore is required for ensure_bucket. Install python-tools-storage[s3]."
        ) from exc

    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)


def put_bytes(
    client: Any,
    *,
    bucket: str,
    key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    sse: str | None = "AES256",
) -> str:
    """Upload bytes with SSE-S3 by default. Returns the validated key."""
    object_key = safe_key(key)
    extra: dict[str, Any] = {
        "Bucket": bucket,
        "Key": object_key,
        "Body": data,
        "ContentType": content_type,
    }
    if sse:
        extra["ServerSideEncryption"] = sse
    client.put_object(**extra)
    return object_key


def presign_get(
    client: Any,
    *,
    bucket: str,
    key: str,
    expires_in: int = 3600,
) -> str:
    """Generate a GET presigned URL with TTL (seconds)."""
    object_key = safe_key(key)
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expires_in,
    )
    return str(url)


def presign_put(
    client: Any,
    *,
    bucket: str,
    key: str,
    expires_in: int = 3600,
    content_type: str = "application/octet-stream",
) -> str:
    """Generate a PUT presigned URL with TTL (seconds)."""
    object_key = safe_key(key)
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": object_key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )
    return str(url)
