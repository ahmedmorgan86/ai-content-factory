"""
AI Content Factory - Central Configuration & Environment Manager
Loads configuration safely from environment variables or settings database.
Adheres to security rule: NEVER hardcode API keys.
"""

import os
import csv
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = bool(os.getenv("VERCEL"))

if IS_VERCEL:
    TMP_ROOT = Path("/tmp/ai-content-factory")
    DB_DIR = TMP_ROOT / "database"
    STORAGE_ROOT = TMP_ROOT / "storage" / "AI Content Factory" / "2026"
    PROMPTS_DIR = BASE_DIR / "prompts"

    # Seed /tmp folders from repo if not yet present
    try:
        if not DB_DIR.exists():
            DB_DIR.mkdir(parents=True, exist_ok=True)
            repo_db = BASE_DIR / "database"
            if repo_db.exists():
                for item in repo_db.glob("*"):
                    if item.is_file():
                        shutil.copy2(item, DB_DIR / item.name)

        if not STORAGE_ROOT.exists():
            STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
            repo_storage = BASE_DIR / "storage" / "AI Content Factory" / "2026"
            if repo_storage.exists():
                for sub in repo_storage.glob("*"):
                    dest = STORAGE_ROOT / sub.name
                    if sub.is_dir() and not dest.exists():
                        shutil.copytree(sub, dest)
                    elif sub.is_file() and not dest.exists():
                        shutil.copy2(sub, dest)
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
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
    
    # Defaults
    NICHE = "Technology & Artificial Intelligence"
    LANGUAGE = "Egyptian Arabic"
    COUNTRY = "Egypt / Arab World"
    IDEAS_PER_BATCH = 20
    CONTENT_STYLE = "Educational, Engaging, Professional, Conversational"
    BRAND_COLORS = ["#0F172A", "#38BDF8", "#818CF8"]
    BRAND_IDENTITY = "Future Tech Navigator"
    
    @classmethod
    def load_from_settings_csv(cls):
        """Loads settings from database/Settings.csv if present."""
        settings_path = DB_DIR / "Settings.csv"
        if not settings_path.exists():
            return
        
        with open(settings_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    k, v = row[0].strip(), row[1].strip()
                    if k == "niche": cls.NICHE = v
                    elif k == "language": cls.LANGUAGE = v
                    elif k == "country": cls.COUNTRY = v
                    elif k == "ideas_per_batch": cls.IDEAS_PER_BATCH = int(v) if v.isdigit() else 20
                    elif k == "content_style": cls.CONTENT_STYLE = v
                    elif k == "brand_identity": cls.BRAND_IDENTITY = v

Config.load_from_settings_csv()
