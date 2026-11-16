"""Firestore metadata adapter, enabled only when server credentials are set.

The application remains runnable locally with its CSV adapter. On Vercel,
configure a Firestore project and service account before enabling this store.
No secret is accepted from a request or returned by this module.
"""
import json
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
        account = json.loads(Config.FIREBASE_SERVICE_ACCOUNT_JSON)
        firebase_admin.initialize_app(
            credentials.Certificate(account),
            {"projectId": Config.FIRESTORE_PROJECT_ID},
        )
    return firestore.client()


def enabled():
    return bool(Config.FIRESTORE_PROJECT_ID and Config.FIREBASE_SERVICE_ACCOUNT_JSON)


def health():
    return {"configured": enabled(), "provider": "Firestore" if enabled() else "CSV (local/temporary)"}


def get_ideas():
    client = _client()
    if client is None:
        return None
    docs = client.collection("ideas").stream()
    return [doc.to_dict() for doc in docs]


def put_ideas(ideas):
    client = _client()
    if client is None:
        return False
    batch = client.batch()
    collection = client.collection("ideas")
    for idea in ideas:
        idea_id = str(idea.get("idea_id") or idea.get("Idea ID") or "")
        if not idea_id or len(idea_id) > 100 or "/" in idea_id:
            continue
        record = dict(idea)
        record.setdefault("idea_id", idea_id)
        batch.set(collection.document(idea_id), record, merge=True)
    batch.commit()
    return True


def update_idea_status(idea_id, new_status):
    client = _client()
    if client is None:
        return False
    ref = client.collection("ideas").document(idea_id)
    if not ref.get().exists:
        return False
    ref.set({"Status": new_status, "status": new_status}, merge=True)
    return True

