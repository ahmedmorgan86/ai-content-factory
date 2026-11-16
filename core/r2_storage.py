"""Cloudflare R2 S3-compatible file storage helpers (optional)."""
from functools import lru_cache
from urllib.parse import quote

from core.config import Config


def enabled():
    return all((Config.R2_ACCOUNT_ID, Config.R2_ACCESS_KEY_ID,
                Config.R2_SECRET_ACCESS_KEY, Config.R2_BUCKET))


def health():
    return {"configured": enabled(), "provider": "Cloudflare R2" if enabled() else "local files (temporary on Vercel)"}


@lru_cache(maxsize=1)
def _client():
    if not enabled():
        return None
    import boto3
    from botocore.config import Config as BotoConfig
    return boto3.client(
        "s3",
        endpoint_url=f"https://{Config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=Config.R2_ACCESS_KEY_ID,
        aws_secret_access_key=Config.R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=BotoConfig(signature_version="s3v4"),
    )


def put_file(path, object_key, content_type=None):
    client = _client()
    if client is None:
        return None
    extra = {"ContentType": content_type} if content_type else {}
    client.upload_file(str(path), Config.R2_BUCKET, object_key, ExtraArgs=extra)
    if Config.R2_PUBLIC_BASE_URL:
        return f"{Config.R2_PUBLIC_BASE_URL.rstrip('/')}/{quote(object_key, safe='/')}"
    return client.generate_presigned_url(
        "get_object", Params={"Bucket": Config.R2_BUCKET, "Key": object_key}, ExpiresIn=3600
    )


def get_file(object_key):
    client = _client()
    if client is None:
        return None
    return client.get_object(Bucket=Config.R2_BUCKET, Key=object_key)
