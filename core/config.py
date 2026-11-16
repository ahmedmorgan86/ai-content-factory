"""
AI Content Factory - Central Configuration & Environment Manager
Loads configuration safely from environment variables or settings database.
Adheres to security rule: NEVER hardcode API keys.
"""

import os
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = bool(os.getenv("VERCEL"))

def _load_dotenv(path: Path):
    """Lightweight .env loader so local runs can pick up saved keys without extra deps."""
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and (k not in os.environ or os.environ.get(k, "") == ""):
                os.environ[k] = v
    except Exception:
        pass

_load_dotenv(BASE_DIR / ".env")

if IS_VERCEL:
    TMP_ROOT = Path("/tmp/ai-content-factory")
    DB_DIR = TMP_ROOT / "database"
    STORAGE_ROOT = TMP_ROOT / "storage" / "AI Content Factory" / "2026"
    PROMPTS_DIR = BASE_DIR / "prompts"

    # Serverless writable storage is ephemeral. Never present the seeded copy as
    # a durable database; persistent storage must be configured separately.
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[!] Warning initializing /tmp for Vercel: {e}")
else:
    DB_DIR = BASE_DIR / "database"
    STORAGE_ROOT = BASE_DIR / "storage" / "AI Content Factory" / "2026"
    PROMPTS_DIR = BASE_DIR / "prompts"

# Ensure runtime directories exist safely
try:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

class Config:
    # Security Credentials (Loaded from Environment)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    GOOGLE_TTS_MODEL = os.getenv("GOOGLE_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    GOOGLE_IMAGE_MODEL = os.getenv("GOOGLE_IMAGE_MODEL", "")
    GOOGLE_USE_IMAGEN = os.getenv("GOOGLE_USE_IMAGEN", "false").lower() == "true"
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
    # GitHub storage (optional, e.g. for free asset persistence on Vercel)
    GITHUB_STORAGE_TOKEN = os.getenv("GITHUB_STORAGE_TOKEN", "")
    GITHUB_STORAGE_REPO = os.getenv("GITHUB_STORAGE_REPO", "")  # owner/repo
    GITHUB_STORAGE_BRANCH = os.getenv("GITHUB_STORAGE_BRANCH", "main")
    GITHUB_STORAGE_PATH = os.getenv("GITHUB_STORAGE_PATH", "storage-assets")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
    # Firestore is an optional durable metadata store. Local development keeps
    # the CSV adapter until credentials are explicitly configured.
    FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "")
    FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET = os.getenv("R2_BUCKET", "")
    R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL", "")
    APP_ADMIN_TOKEN = os.getenv("APP_ADMIN_TOKEN", "")
    
    # Defaults
    NICHE = "Technology & Artificial Intelligence"
    LANGUAGE = "Egyptian Arabic"
    COUNTRY = "Egypt / Arab World"
    IDEAS_PER_BATCH = 20
    CONTENT_STYLE = "Educational, Engaging, Professional, Conversational"
    BRAND_COLORS = ["#30483A", "#B75E43", "#D7BD7A"]
    BRAND_IDENTITY = "مِداد"
    
    @classmethod
    def load_from_settings_csv(cls):
        """Loads settings from Firestore when configured, else from Settings.csv."""
        # Prefer Firestore (durable / cloud) as source of truth when enabled.
        try:
            store = __import__("core.firestore_store", fromlist=["enabled", "get_settings"])
            if store.enabled():
                items = store.get_settings() or {}
                if items:
                    for k, item in items.items():
                        v = item.get("value", "") if isinstance(item, dict) else str(item)
                        cls._apply_setting(k, v)
                    return
        except Exception as e:
            print(f"[!] Warning loading settings from Firestore: {e}")

        settings_path = DB_DIR / "Settings.csv"
        if not settings_path.exists():
            return

        with open(settings_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    cls._apply_setting(row[0].strip(), row[1].strip())

    @classmethod
    def _apply_setting(cls, k, v):
        if k == "niche":
            cls.NICHE = v
        elif k == "language":
            cls.LANGUAGE = v
        elif k == "country":
            cls.COUNTRY = v
        elif k == "ideas_per_batch":
            cls.IDEAS_PER_BATCH = int(v) if str(v).isdigit() else 20
        elif k == "content_style":
            cls.CONTENT_STYLE = v
        elif k == "brand_identity":
            cls.BRAND_IDENTITY = v

    @classmethod
    def set_runtime_env(cls, updates: dict):
        env_path = BASE_DIR / ".env"
        existing = {}
        if env_path.exists():
            try:
                for raw in env_path.read_text(encoding="utf-8").splitlines():
                    if "=" in raw and not raw.strip().startswith("#"):
                        k, v = raw.split("=", 1)
                        existing[k.strip()] = v
            except Exception:
                existing = {}
        for k, v in updates.items():
            if v is None:
                continue
            os.environ[k] = str(v)
            existing[k] = str(v)
            if hasattr(cls, k):
                setattr(cls, k, str(v))
        try:
            lines = [f"{k}={v}" for k, v in existing.items()]
            env_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        except Exception:
            pass

Config.load_from_settings_csv()
