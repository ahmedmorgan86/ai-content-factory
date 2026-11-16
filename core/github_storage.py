"""GitHub repository storage helpers (optional).

Stores generated assets in a GitHub repo (e.g. under storage-assets/<idea_id>/...).
Requires a token with contents write access for uploads and read for private repos.
"""
import base64
import io
import mimetypes
import os
from functools import lru_cache

import requests

from core.config import Config


def _repo():
    return (getattr(Config, "GITHUB_STORAGE_REPO", "") or "").strip()


def _branch():
    return (getattr(Config, "GITHUB_STORAGE_BRANCH", "") or "main").strip() or "main"


def _prefix():
    p = (getattr(Config, "GITHUB_STORAGE_PATH", "") or "storage-assets").strip().strip("/")
    return p


def _token():
    return (getattr(Config, "GITHUB_STORAGE_TOKEN", "") or "").strip()


def enabled():
    return bool(_repo() and _token())


def health():
    repo = _repo()
    ok = False
    err = None
    if enabled():
        try:
            r = _request("GET", f"/repos/{repo}")
            if r.status_code == 200:
                ok = True
            else:
                err = f"GitHub API {r.status_code}"
        except Exception as e:
            err = str(e)
    return {
        "configured": enabled(),
        "ok": ok,
        "provider": "GitHub" if enabled() else "not configured",
        "repo": repo if enabled() else "",
        "branch": _branch() if enabled() else "",
        "error": err,
    }


def _headers(accept="application/vnd.github+json"):
    h = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-content-factory",
    }
    tok = _token()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def _request(method, path, **kwargs):
    url = f"https://api.github.com{path}"
    kwargs.setdefault("timeout", 60)
    headers = kwargs.pop("headers", None) or _headers()
    return requests.request(method, url, headers=headers, **kwargs)


def _object_path(object_key: str):
    key = str(object_key).replace("\\", "/").lstrip("/")
    prefix = _prefix()
    return f"{prefix}/{key}" if prefix else key


def put_file(path, object_key, content_type=None):
    if not enabled():
        return None
    repo = _repo()
    branch = _branch()
    obj_path = _object_path(object_key)
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")

    # get existing sha if file exists
    sha = None
    try:
        r = _request("GET", f"/repos/{repo}/contents/{obj_path}", params={"ref": branch})
        if r.status_code == 200:
            sha = (r.json() or {}).get("sha")
    except Exception:
        sha = None

    payload = {
        "message": f"Add/update asset {obj_path}",
        "content": b64,
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    r = _request("PUT", f"/repos/{repo}/contents/{obj_path}", json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub upload failed ({r.status_code}): {r.text[:300]}")
    j = r.json() or {}
    content = j.get("content") or {}
    download_url = content.get("download_url")
    html_url = content.get("html_url")
    return download_url or html_url


def get_file(object_key):
    if not enabled():
        return None
    repo = _repo()
    branch = _branch()
    obj_path = _object_path(object_key)

    # Try raw content via API (works for private repos with token, up to 100MB)
    try:
        r = _request(
            "GET",
            f"/repos/{repo}/contents/{obj_path}",
            params={"ref": branch},
            headers=_headers(accept="application/vnd.github.raw"),
        )
        if r.status_code == 200:
            ct = r.headers.get("Content-Type") or mimetypes.guess_type(obj_path)[0] or "application/octet-stream"
            # If GitHub returns JSON (e.g. for some cases), avoid mis-serving; raw accept should give bytes
            if "application/json" in ct and len(r.content) and r.content[:1] in (b"{", b"["):
                # fallback: parse and decode base64 if present
                try:
                    j = r.json()
                    if isinstance(j, dict) and j.get("encoding") == "base64" and j.get("content"):
                        raw = base64.b64decode(j["content"])
                        return {"Body": io.BytesIO(raw), "ContentType": mimetypes.guess_type(obj_path)[0] or "application/octet-stream"}
                except Exception:
                    pass
            return {"Body": io.BytesIO(r.content), "ContentType": ct.split(";")[0].strip()}
        if r.status_code == 404:
            return None
    except Exception:
        pass

    # Fallback: raw.githubusercontent for public repos
    try:
        raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{obj_path}"
        r = requests.get(raw_url, timeout=60)
        if r.status_code == 200:
            ct = r.headers.get("Content-Type") or mimetypes.guess_type(obj_path)[0] or "application/octet-stream"
            return {"Body": io.BytesIO(r.content), "ContentType": ct.split(";")[0].strip()}
    except Exception:
        pass
    return None
