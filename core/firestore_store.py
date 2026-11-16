"""Firestore data adapter.

When configured, this module is the source of truth for app data (ideas,
settings, scripts, seo, analytics, publishing records, etc.) so the app can run
in "Firestore only" mode without relying on CSV files for persistence.
No secrets are accepted from requests or returned by this module.
"""
import json
import datetime
from functools import lru_cache

from core.config import Config


@lru_cache(maxsize=1)
def _client():
    if not Config.FIRESTORE_PROJECT_ID or not Config.FIREBASE_SERVICE_ACCOUNT_JSON:
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise RuntimeError("Firestore is configured but firebase-admin is not installed") from exc

    if not firebase_admin._apps:
        try:
            account = json.loads(Config.FIREBASE_SERVICE_ACCOUNT_JSON)
        except Exception as exc:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc
        firebase_admin.initialize_app(
            credentials.Certificate(account),
            {"projectId": Config.FIRESTORE_PROJECT_ID},
        )
    return firestore.client()


def _server_timestamp():
    try:
        from google.cloud import firestore as gcf
        return gcf.SERVER_TIMESTAMP
    except Exception:
        return datetime.datetime.utcnow().isoformat()


def enabled():
    return bool(Config.FIRESTORE_PROJECT_ID and Config.FIREBASE_SERVICE_ACCOUNT_JSON)


def health():
    ok = False
    err = None
    if enabled():
        try:
            # lightweight check: ensure client can be constructed
            _client()
            ok = True
        except Exception as e:
            err = str(e)
    return {
        "configured": enabled(),
        "ok": ok,
        "provider": "Firestore" if enabled() else "CSV (local/temporary)",
        "error": err,
    }


def _safe_doc_id(value: str) -> str:
    value = str(value or "").strip().replace("/", "_")
    return value[:150]


def get_collection(name):
    client = _client()
    if client is None:
        return None
    docs = client.collection(name).stream()
    items = []
    for doc in docs:
        data = doc.to_dict() or {}
        data.setdefault("_id", doc.id)
        items.append(data)
    return items


def get_document(collection_name, doc_id):
    client = _client()
    if client is None:
        return None
    ref = client.collection(collection_name).document(_safe_doc_id(doc_id))
    snap = ref.get()
    if not snap.exists:
        return {}
    data = snap.to_dict() or {}
    data.setdefault("_id", snap.id)
    return data


def set_document(collection_name, doc_id, data, merge=True):
    client = _client()
    if client is None:
        return False
    payload = dict(data or {})
    payload.setdefault("_updated_at", _server_timestamp())
    client.collection(collection_name).document(_safe_doc_id(doc_id)).set(payload, merge=merge)
    return True


def add_record(collection_name, data, doc_id=None):
    client = _client()
    if client is None:
        return False
    payload = dict(data or {})
    payload.setdefault("_created_at", _server_timestamp())
    col = client.collection(collection_name)
    if doc_id:
        col.document(_safe_doc_id(doc_id)).set(payload, merge=True)
    else:
        col.add(payload)
    return True


def query_by_field(collection_name, field, value):
    client = _client()
    if client is None:
        return None
    docs = client.collection(collection_name).where(field, "==", value).stream()
    items = []
    for doc in docs:
        data = doc.to_dict() or {}
        data.setdefault("_id", doc.id)
        items.append(data)
    return items


# ---- Ideas ----

def get_ideas():
    items = get_collection("ideas")
    if items is None:
        return None
    return items


def put_ideas(ideas):
    client = _client()
    if client is None:
        return False
    batch = client.batch()
    collection = client.collection("ideas")
    for idea in ideas:
        idea_id = str(idea.get("idea_id") or idea.get("Idea ID") or "")
        if not idea_id or len(idea_id) > 150 or "/" in idea_id:
            continue
        record = dict(idea)
        record.setdefault("idea_id", idea_id)
        record.setdefault("Idea ID", idea_id)
        batch.set(collection.document(idea_id), record, merge=True)
    batch.commit()
    return True


def update_idea_status(idea_id, new_status):
    client = _client()
    if client is None:
        return False
    ref = client.collection("ideas").document(_safe_doc_id(idea_id))
    if not ref.get().exists:
        return False
    ref.set({"Status": new_status, "status": new_status, "_updated_at": _server_timestamp()}, merge=True)
    return True


# ---- Settings ----

SETTINGS_DOC = "workspace"

def get_settings():
    if not enabled():
        return None
    doc = get_document("settings", SETTINGS_DOC)
    if doc is None:
        return None
    return doc.get("items", {})


def save_settings(items: dict):
    if not enabled():
        return False
    return set_document("settings", SETTINGS_DOC, {"items": items, "type": "workspace_settings"}, merge=True)


# ---- Generic table-like records ----

def get_records(collection_name):
    return get_collection(collection_name)


def save_record(collection_name, record, doc_id=None):
    return add_record(collection_name, record, doc_id=doc_id)


def get_records_by(collection_name, field, value):
    return query_by_field(collection_name, field, value)

