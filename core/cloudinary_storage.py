"""Cloudinary storage helpers (optional, free tier available).

Used as an alternative to Firebase Storage / R2 for persisting generated assets.
Uploads are stored under folder ai-content-factory/<idea_id>/...
"""
import hashlib
import time
from functools import lru_cache
import requests

from core.config import Config


def enabled():
    return bool(Config.CLOUDINARY_CLOUD_NAME and Config.CLOUDINARY_API_KEY and Config.CLOUDINARY_API_SECRET)


def health():
    return {
        "configured": enabled(),
        "ok": bool(enabled()),
        "provider": "Cloudinary" if enabled() else "not configured",
        "error": None,
    }


def _resource_type_for(key: str, content_type: str = ""):
    ct = (content_type or "").lower()
    k = (key or "").lower()
    if ct.startswith("image/") or k.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return "image"
    if ct.startswith("video/") or k.endswith((".mp4", ".mov", ".webm")):
        return "video"
    # audio wav/mp3 and other files -> raw in Cloudinary
    return "raw"


def _public_id(object_key: str):
    # Keep extension-less id stable-ish; include key path for organization
    key = object_key.replace("\\", "/").lstrip("/")
    base = "ai-content-factory/" + key
    # Cloudinary public_id can include folders; strip leading slashes
    return base


def _signature(params: dict):
    # Cloudinary signature: sha1 of sorted "k=v&..." + api_secret
    items = sorted((k, v) for k, v in params.items() if v is not None and v != "")
    to_sign = "&".join(f"{k}={v}" for k, v in items) + Config.CLOUDINARY_API_SECRET
    return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()


@lru_cache(maxsize=256)
def _uploaded_url_cache(object_key: str):
    return None


# simple in-memory map for current process (urls discovered after upload)
_URLS = {}


def put_file(path, object_key, content_type=None):
    if not enabled():
        return None
    resource_type = _resource_type_for(object_key, content_type or "")
    public_id = _public_id(object_key)
    timestamp = int(time.time())
    params = {
        "public_id": public_id,
        "timestamp": timestamp,
        # overwrite so re-runs update asset
        "overwrite": "true",
        "invalidate": "true",
    }
    # raw resources keep filename/extension behavior; keep public_id explicit
    signature = _signature(params)
    url = f"https://api.cloudinary.com/v1_1/{Config.CLOUDINARY_CLOUD_NAME}/{resource_type}/upload"
    data = {
        **params,
        "api_key": Config.CLOUDINARY_API_KEY,
        "signature": signature,
    }
    with open(path, "rb") as f:
        files = {"file": f}
        resp = requests.post(url, data=data, files=files, timeout=120)
    resp.raise_for_status()
    j = resp.json()
    secure_url = j.get("secure_url") or j.get("url")
    _URLS[object_key] = {"url": secure_url, "resource_type": resource_type, "public_id": public_id}
    return secure_url


def get_file(object_key):
    if not enabled():
        return None
    info = _URLS.get(object_key)
    # Best-effort: try to construct URL by probing common resource types if not known.
    # For reliable fetch across process restarts, a persistent index would be needed.
    urls = []
    if info and info.get("url"):
        urls.append((info["url"], info.get("resource_type")))
    # Guess common delivery URLs
    base = f"https://res.cloudinary.com/{Config.CLOUDINARY_CLOUD_NAME}"
    pid = _public_id(object_key)
    urls.extend([
        (f"{base}/image/upload/{pid}", "image"),
        (f"{base}/video/upload/{pid}", "video"),
        (f"{base}/raw/upload/{pid}", "raw"),
    ])
    for u, rt in urls:
        try:
            r = requests.get(u, timeout=60)
            if r.status_code == 200:
                ct = r.headers.get("Content-Type") or "application/octet-stream"
                return {"Body": __import__("io").BytesIO(r.content), "ContentType": ct}
        except Exception:
            continue
    return None