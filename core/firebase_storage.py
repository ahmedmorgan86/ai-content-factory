"""Firebase Storage helpers (optional), using the same Firebase service account.

Alternative to Cloudflare R2 for persisting generated assets when running on
ephemeral filesystems (e.g. Vercel). Requires Firebase Storage bucket to exist.
"""
from functools import lru_cache

from core.config import Config


def _bucket_name():
    bucket = (Config.FIREBASE_STORAGE_BUCKET or "").strip()
    if bucket:
        return bucket
    if Config.FIRESTORE_PROJECT_ID:
        return f"{Config.FIRESTORE_PROJECT_ID}.firebasestorage.app"
    return ""


def enabled():
    return bool(Config.FIREBASE_SERVICE_ACCOUNT_JSON and (Config.FIREBASE_STORAGE_BUCKET or Config.FIRESTORE_PROJECT_ID))


def health():
    name = _bucket_name()
    ok = False
    err = None
    if enabled():
        try:
            _bucket()
            ok = True
        except Exception as e:
            err = str(e)
    return {
        "configured": enabled(),
        "ok": ok,
        "provider": "Firebase Storage" if enabled() else "not configured",
        "bucket": name if enabled() else "",
        "error": err,
    }


@lru_cache(maxsize=1)
def _bucket():
    if not enabled():
        return None
    # Ensure firebase_admin app is initialized (shared with Firestore)
    from core import firestore_store
    firestore_store._client()
    try:
        from firebase_admin import storage
    except Exception as exc:
        raise RuntimeError("firebase-admin storage is unavailable") from exc
    name = _bucket_name()
    if not name:
        raise RuntimeError("Firebase Storage bucket is not configured")
    return storage.bucket(name=name)


def put_file(path, object_key, content_type=None):
    bucket = _bucket()
    if bucket is None:
        return None
    blob = bucket.blob(object_key)
    blob.upload_from_filename(str(path), content_type=content_type)
    # Prefer signed URL for private buckets; fallback to public URL form if accessible.
    try:
        import datetime
        return blob.generate_signed_url(expiration=datetime.timedelta(hours=1), method="GET")
    except Exception:
        try:
            blob.make_public()
            return blob.public_url
        except Exception:
            return None


def get_file(object_key):
    bucket = _bucket()
    if bucket is None:
        return None
    blob = bucket.blob(object_key)
    if not blob.exists():
        return None
    data = blob.download_as_bytes()
    blob.reload()
    return {
        "Body": __import__("io").BytesIO(data),
        "ContentType": blob.content_type or "application/octet-stream",
    }