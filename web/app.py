"""
AI Content Factory - Web Command Center & Automation Controller
FastAPI Backend providing REST APIs and serving the responsive Arabic/English UI.
"""

import os
import sys
import json
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.config import Config, DB_DIR, STORAGE_ROOT, BASE_DIR
from core.idea_engine import IdeaEngine
from core.script_engine import ScriptEngine
from core.seo_engine import SEOEngine
from core.thumbnail_engine import ThumbnailEngine
from core.storage_engine import StorageEngine
from core.publishing_engine import PublishingEngine
from core.analytics_engine import AnalyticsEngine
from core.telegram_bot import TelegramControlPanel
from core.voice_engine import VoiceEngine
from core.video_engine import VideoEngine

app = FastAPI(
    title="AI Content Factory Command Center",
    description="Autonomous Content Engine Dashboard & Controller",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("APP_ORIGIN", "http://127.0.0.1:8000"), "http://localhost:8000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def require_admin_token(request: Request, call_next):
    """Protect API endpoints when a deployment admin token is configured."""
    from core.config import Config as AppConfig
    if request.url.path == "/api/auth/status":
        return await call_next(request)
    if AppConfig.APP_ADMIN_TOKEN and request.url.path.startswith("/api/"):
        supplied = request.headers.get("authorization", "")
        if not supplied.startswith("Bearer ") or not __import__("hmac").compare_digest(
            supplied[7:], AppConfig.APP_ADMIN_TOKEN
        ):
            return JSONResponse({"detail": "يلزم تسجيل الدخول قبل استخدام التطبيق."}, status_code=401)
    return await call_next(request)

# Directories
STATIC_DIR = Path(__file__).resolve().parent / "static"
try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

STORAGE_DIR = BASE_DIR / "storage"

# Mount static folder safely
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/api/thumbnail/{idea_id}/{filename}")
async def serve_thumbnail(idea_id: str, filename: str):
    """Serves generated thumbnail file safely across local and serverless environments."""
    if Path(idea_id).name != idea_id or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    target = STORAGE_ROOT / idea_id / "Thumbnails" / filename
    if target.exists() and target.is_file():
        return FileResponse(target)
    fallback = BASE_DIR / "storage" / "AI Content Factory" / "2026" / idea_id / "Thumbnails" / filename
    if fallback.exists() and fallback.is_file():
        return FileResponse(fallback)
    from core.r2_storage import get_file, enabled
    if enabled():
        try:
            obj = get_file(f"{idea_id}/Thumbnails/{filename}")
            return Response(content=obj["Body"].read(), media_type=obj.get("ContentType", "image/jpeg"))
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Thumbnail not found")

@app.get("/api/audio/{idea_id}/{filename}")
async def serve_audio(idea_id: str, filename: str):
    """Serves generated VoxArabic voiceover audio file."""
    if Path(idea_id).name != idea_id or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    target = STORAGE_ROOT / idea_id / "Audio" / filename
    if target.exists() and target.is_file():
        return FileResponse(target, media_type="audio/wav" if target.suffix.lower() == ".wav" else "audio/mpeg")
    fallback = BASE_DIR / "storage" / "AI Content Factory" / "2026" / idea_id / "Audio" / filename
    if fallback.exists() and fallback.is_file():
        return FileResponse(fallback, media_type="audio/wav" if fallback.suffix.lower() == ".wav" else "audio/mpeg")
    from core.r2_storage import get_file, enabled
    if enabled():
        try:
            obj = get_file(f"{idea_id}/Audio/{filename}")
            return Response(content=obj["Body"].read(), media_type=obj.get("ContentType", "audio/mpeg"))
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Audio file not found")

@app.get("/api/video/{idea_id}/{filename}")
async def serve_video(idea_id: str, filename: str):
    """Serves rendered MP4 ready-to-publish video file."""
    if Path(idea_id).name != idea_id or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    target = STORAGE_ROOT / idea_id / "Video_Assets" / filename
    if target.exists() and target.is_file():
        return FileResponse(target, media_type="video/mp4")
    fallback = BASE_DIR / "storage" / "AI Content Factory" / "2026" / idea_id / "Video_Assets" / filename
    if fallback.exists() and fallback.is_file():
        return FileResponse(fallback, media_type="video/mp4")
    from core.r2_storage import get_file, enabled
    if enabled():
        try:
            obj = get_file(f"{idea_id}/Video_Assets/{filename}")
            return Response(content=obj["Body"].read(), media_type="video/mp4")
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Video file not found")

@app.get("/api/scene-frame/{idea_id}/{filename}")
async def serve_scene_frame(idea_id: str, filename: str):
    """Serves generated AI scene visual frame."""
    if Path(idea_id).name != idea_id or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    target = STORAGE_ROOT / idea_id / "Video_Assets" / filename
    if target.exists() and target.is_file():
        return FileResponse(target, media_type="image/jpeg")
    fallback = BASE_DIR / "storage" / "AI Content Factory" / "2026" / idea_id / "Video_Assets" / filename
    if fallback.exists() and fallback.is_file():
        return FileResponse(fallback, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Scene frame not found")

@app.get("/storage/{file_path:path}")
async def serve_storage_file(file_path: str):
    """Serves files from storage safely across local and Vercel environments."""
    from core.config import IS_VERCEL
    if Path(file_path).is_absolute():
        raise HTTPException(status_code=400, detail="Invalid storage path")
    roots = [Path("/tmp/ai-content-factory/storage"), BASE_DIR / "storage"] if IS_VERCEL else [BASE_DIR / "storage"]
    for root in roots:
        candidate = (root / file_path).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="File not found")

# Initialize engines
idea_engine = IdeaEngine()
script_engine = ScriptEngine()
seo_engine = SEOEngine()
thumbnail_engine = ThumbnailEngine()
storage_engine = StorageEngine()
publishing_engine = PublishingEngine()
analytics_engine = AnalyticsEngine()
telegram_bot = TelegramControlPanel()
voice_engine = VoiceEngine()
video_engine = VideoEngine()


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Returns empty icon to prevent browser 404 noise."""
    return Response(content=b"", media_type="image/x-icon", status_code=204)

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main dashboard application."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        index_file = BASE_DIR / "web" / "static" / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>AI Content Factory Dashboard loading...</h1>")
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    if Config.APP_ADMIN_TOKEN:
        content = content.replace('<div id="admin-access-panel" class="hidden', '<div id="admin-access-panel" class="')
    return HTMLResponse(content=content)


@app.get("/api/overview")
async def get_overview():
    """Retrieves high-level KPIs, activity feeds, and system health status."""
    ideas = idea_engine.get_all_ideas()
    analytics_records = analytics_engine.get_all_metrics()

    total_ideas = len(ideas)
    long_count = sum(1 for i in ideas if i.get("Video Type") == "Long-form")
    short_count = sum(1 for i in ideas if i.get("Video Type") == "Short-form")
    ready_count = sum(1 for i in ideas if "Ready" in i.get("Status", "") or "Approved" in i.get("Status", ""))

    total_views = sum(int(float(r.get("Views", 0) or 0)) for r in analytics_records)
    total_watch = sum(int(float(r.get("Watch Time (Mins)", 0) or 0)) for r in analytics_records)
    total_subs = sum(int(float(r.get("Subscribers Growth", 0) or 0)) for r in analytics_records)
    avg_ctr = round(sum(float(r.get("CTR (%)", 0) or 0) for r in analytics_records) / (len(analytics_records) or 1), 1)

    from core.firestore_store import health as firestore_health
    from core.r2_storage import health as r2_health
    return {
        "status": "online",
        "system_time": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        "data_store": firestore_health(),
        "file_store": r2_health(),
        "kpis": {
            "total_ideas": total_ideas,
            "short_ideas": short_count,
            "long_ideas": long_count,
            "ready_packages": ready_count,
            "total_views": total_views,
            "total_watch_hours": round(total_watch / 60, 1),
            "total_subscribers": total_subs,
            "avg_ctr": avg_ctr,
            "has_analytics": bool(analytics_records)
        },
        "config": {
            "niche": Config.NICHE,
            "language": Config.LANGUAGE,
            "brand_identity": Config.BRAND_IDENTITY,
            "brand_colors": Config.BRAND_COLORS
        },
        "recent_ideas": ideas[-6:] if ideas else []
    }


@app.get("/api/ideas")
async def list_ideas(
    type: Optional[str] = Query(None, description="Filter by Long-form or Short-form"),
    search: Optional[str] = Query(None, description="Search keyword in title or summary")
):
    """Returns list of ideas from database with optional filtering."""
    ideas = idea_engine.get_all_ideas()
    filtered = ideas

    if type and type.lower() != "all":
        filtered = [i for i in filtered if i.get("Video Type", "").lower() == type.lower()]

    if search:
        kw = search.strip().lower()
        filtered = [
            i for i in filtered 
            if kw in i.get("Video Title", "").lower()
            or kw in i.get("Video Summary", "").lower()
            or kw in i.get("SEO Keywords", "").lower()
        ]

    # Reverse so newest appear first
    return {"ideas": list(reversed(filtered)), "count": len(filtered)}


@app.post("/api/ideas/generate")
async def generate_ideas_batch():
    """Generates a fresh batch of 20 unique scored ideas."""
    try:
        new_ideas = idea_engine.generate_batch()
        saved_count = idea_engine.save_ideas_to_database(new_ideas)
        return {
            "success": True,
            "generated_count": len(new_ideas),
            "saved_count": saved_count,
            "ideas": new_ideas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/production/{idea_id}")
async def get_production_package(idea_id: str):
    """Retrieves all produced assets for a specific idea ID."""
    if Path(idea_id).name != idea_id or idea_id in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid idea_id")
    video_dir = STORAGE_ROOT / idea_id
    if not video_dir.exists():
        # Check if idea exists in database
        ideas = idea_engine.get_all_ideas()
        matching = next((i for i in ideas if i.get("Idea ID") == idea_id), None)
        return {
            "produced": False,
            "idea_id": idea_id,
            "idea": matching
        }

    # Gather assets
    scripts_dir = video_dir / "Scripts"
    seo_dir = video_dir / "SEO"
    thumb_dir = video_dir / "Thumbnails"

    script_md_content = ""
    scenes_data = []
    if scripts_dir.exists():
        for f in scripts_dir.glob("*.md"):
            with open(f, "r", encoding="utf-8") as sf:
                script_md_content = sf.read()
        for f in scripts_dir.glob("scenes_*.json"):
            with open(f, "r", encoding="utf-8") as jf:
                scenes_data = json.load(jf)

    seo_data = {}
    if seo_dir.exists():
        for f in seo_dir.glob("*.json"):
            with open(f, "r", encoding="utf-8") as jf:
                seo_data = json.load(jf)

    # Check thumbnails and build web-relative URL paths
    thumbnails = {}
    if thumb_dir.exists():
        yt_thumb = list(thumb_dir.glob("*youtube_1280x720.jpg"))
        vert_thumb = list(thumb_dir.glob("*vertical_1080x1920.jpg"))
        if yt_thumb:
            thumbnails["youtube_url"] = f"/api/thumbnail/{idea_id}/{yt_thumb[0].name}"
            thumbnails["youtube_path"] = str(yt_thumb[0])
            thumbnails["youtube_dim"] = "1280x720"
        if vert_thumb:
            thumbnails["vertical_url"] = f"/api/thumbnail/{idea_id}/{vert_thumb[0].name}"
            thumbnails["vertical_path"] = str(vert_thumb[0])
            thumbnails["vertical_dim"] = "1080x1920"

    # Check Audio (VoxArabic voiceover)
    audio_dir = video_dir / "Audio"
    audio_data = None
    if audio_dir.exists():
        audio_files = sorted([*audio_dir.glob("*.mp3"), *audio_dir.glob("*.wav")], key=lambda f: f.stat().st_mtime)
        if audio_files:
            latest_audio = audio_files[-1]
            audio_data = {
                "available": True,
                "url": f"/api/audio/{idea_id}/{latest_audio.name}",
                "filename": latest_audio.name,
                "size_kb": round(latest_audio.stat().st_size / 1024, 1),
                "voice_name": next((v["name"] for k, v in voice_engine.get_available_voices().items() if f"_{k}." in latest_audio.name), "Google / Edge TTS"),
                "provider": "Google Gemini TTS" if latest_audio.suffix == ".wav" else "Edge TTS"
            }

    # Check Rendered Videos & Scene Frames
    video_assets_dir = video_dir / "Video_Assets"
    video_data = None
    scene_frames = []
    if video_assets_dir.exists():
        mp4s = list(video_assets_dir.glob("final_video_*.mp4"))
        if mp4s:
            latest_mp4 = mp4s[-1]
            video_data = {
                "available": True,
                "url": f"/api/video/{idea_id}/{latest_mp4.name}",
                "filename": latest_mp4.name,
                "size_mb": round(latest_mp4.stat().st_size / (1024 * 1024), 2),
                "is_vertical": "vertical" in latest_mp4.name.lower()
            }
        # Gather scene frames
        frames = sorted(list(video_assets_dir.glob("frame_scene_*.jpg")))
        for f in frames:
            scene_frames.append({
                "url": f"/api/scene-frame/{idea_id}/{f.name}",
                "filename": f.name
            })

    # Get Publishing status from CSV
    publishing_records = []
    pub_csv = DB_DIR / "Publishing.csv"
    if pub_csv.exists():
        with open(pub_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Idea ID") == idea_id:
                    publishing_records.append(row)

    # Find idea metadata
    ideas = idea_engine.get_all_ideas()
    idea_meta = next((i for i in ideas if i.get("Idea ID") == idea_id), {})

    return {
        "produced": True,
        "idea_id": idea_id,
        "metadata": idea_meta,
        "script_markdown": script_md_content,
        "scenes": scenes_data,
        "seo": seo_data,
        "thumbnails": thumbnails,
        "audio": audio_data,
        "video": video_data,
        "scene_frames": scene_frames,
        "publishing": publishing_records,
        "storage_path": str(video_dir)
    }


@app.post("/api/production/generate")
def generate_production_package(payload: Dict[str, Any] = Body(...)):
    """Runs complete production generation (Scripts, SEO, Thumbnails, Storage, Publishing manifest)."""
    idea_id = payload.get("idea_id")
    if not idea_id:
        raise HTTPException(status_code=400, detail="idea_id is required")

    ideas = idea_engine.get_all_ideas()
    selected_idea = next((i for i in ideas if (i.get("Idea ID") or i.get("idea_id")) == idea_id), None)
    if not selected_idea:
        raise HTTPException(status_code=404, detail=f"Idea {idea_id} not found in database")

    if not Config.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="خدمة التعليق الصوتي غير مهيأة: أضف GEMINI_API_KEY إلى متغيرات Vercel ثم أعد النشر.",
        )

    # Map database row format to engine format
    idea_dict = {
        "idea_id": selected_idea.get("Idea ID") or selected_idea.get("idea_id"),
        "video_title": selected_idea.get("Video Title") or selected_idea.get("video_title", ""),
        "video_summary": selected_idea.get("Video Summary") or selected_idea.get("video_summary", ""),
        "target_audience": selected_idea.get("Target Audience") or selected_idea.get("target_audience", ""),
        "hook": selected_idea.get("Hook") or selected_idea.get("hook", ""),
        "content_angle": selected_idea.get("Content Angle") or selected_idea.get("content_angle", ""),
        "video_type": selected_idea.get("Video Type") or selected_idea.get("video_type", "Short-form"),
        "estimated_duration": selected_idea.get("Estimated Duration") or selected_idea.get("estimated_duration", "60 ثانية"),
        "seo_keywords": [k.strip() for k in (selected_idea.get("SEO Keywords") or ", ".join(selected_idea.get("seo_keywords", []))).split(",") if k.strip()]
    }

    stage = "السكريبت"
    try:
        # 1. Scripts
        short_script = script_engine.generate_short_script(idea_dict)
        long_script = script_engine.generate_long_script(idea_dict)
        script_to_use = short_script if "Short" in idea_dict["video_type"] else long_script
        script_engine.save_script_to_database(script_to_use)

        # 2. SEO Package
        stage = "بيانات SEO"
        seo_pkg = seo_engine.generate_seo_package(idea_dict, script_to_use)
        seo_engine.save_seo_to_database(seo_pkg)

        # 3. Create Storage Structure & stage scripts/SEO
        stage = "حفظ الملفات"
        storage_engine.create_video_structure(idea_id)
        storage_engine.save_script_asset(idea_id, script_to_use)
        storage_engine.save_seo_asset(idea_id, seo_pkg)

        # 4. Generate & Verify Thumbnails (1280x720 & 1080x1920)
        stage = "إنشاء الصور المصغرة"
        target_thumb_dir = STORAGE_ROOT / idea_id / "Thumbnails"
        thumb_res = thumbnail_engine.generate_and_verify_thumbnails(
            idea_id, idea_dict["video_title"], output_dir=target_thumb_dir
        )

        # 5. Prepare Publishing Manifest (Unapproved / Pending by default)
        publishing_engine.prepare_publishing_manifest(
            idea_id, idea_dict["video_title"], seo_pkg, thumb_res, approved=False
        )

        # 6. Generate video-type matched Egyptian Arabic voiceover with Google Gemini TTS.
        stage = "التعليق الصوتي من Google Gemini"
        voice_key = "google_puck" if idea_dict["video_type"] == "Short-form" else "google_charon"
        voice_res = voice_engine.generate_voiceover(
            idea_id=idea_id,
            text=script_to_use["full_voiceover"],
            voice_key=voice_key,
            video_type=idea_dict["video_type"]
        )

        # 7. Render Ready-to-Publish Video (Shorts 9:16 or Long 16:9)
        stage = "تركيب الفيديو"
        video_res = None
        try:
            video_res = video_engine.render_video_for_idea(
                idea_id=idea_id,
                script_data=script_to_use,
                voice_key=voice_key,
                is_vertical=("Short" in idea_dict["video_type"]),
                video_type=idea_dict["video_type"]
            )
        except Exception as vre:
            print(f"Video rendering warning: {vre}")

        # 8. Update status in Ideas.csv
        idea_engine.update_idea_status(idea_id, "Ready for Production")
        try:
            r2_sync = storage_engine.sync_to_r2(idea_id)
        except Exception as storage_error:
            print(f"R2 upload warning for {idea_id}: {type(storage_error).__name__}")
            r2_sync = {"configured": True, "uploaded": 0, "error": "cloud storage sync failed"}

        return {
            "success": True,
            "file_storage": r2_sync,
            "idea_id": idea_id,
            "message": "Full production package generated: Script, SEO, Real AI Thumbnails, Egyptian Voiceover, and Ready-to-Publish Video.",
            "script": script_to_use,
            "seo": seo_pkg,
            "thumbnails": thumb_res,
            "audio": voice_res,
            "video": video_res
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Production generation failed for {idea_id} during {stage}: {type(e).__name__}: {e}")
        status_code = 502 if stage == "التعليق الصوتي من Google Gemini" else 500
        raise HTTPException(
            status_code=status_code,
            detail=f"فشل الإنتاج في مرحلة {stage}. راجع إعدادات الخدمة أو سجل الخادم للتفاصيل.",
        )


@app.post("/api/voice/generate")
def generate_voiceover_endpoint(payload: Dict[str, Any] = Body(...)):
    """Generates authentic Egyptian Arabic voiceover using VoxArabicStudio engine."""
    idea_id = payload.get("idea_id")
    voice_key = payload.get("voice_key", "google_puck")
    custom_text = payload.get("text")
    if not idea_id:
        raise HTTPException(status_code=400, detail="idea_id is required")

    text_to_speak = custom_text
    if not text_to_speak:
        # Load script from storage
        scripts_dir = STORAGE_ROOT / idea_id / "Scripts"
        scene_files = list(scripts_dir.glob("scenes_*.json")) if scripts_dir.exists() else []
        if scene_files:
            with open(scene_files[0], "r", encoding="utf-8") as f:
                scenes = json.load(f)
            text_to_speak = " ".join([s.get("voiceover", "") for s in scenes if s.get("voiceover")])

    if not text_to_speak:
        raise HTTPException(status_code=400, detail="No voiceover text found or provided.")

    try:
        ideas = idea_engine.get_all_ideas()
        idea = next((i for i in ideas if i.get("Idea ID") == idea_id), {})
        res = voice_engine.generate_voiceover(idea_id, text_to_speak, voice_key=voice_key, video_type=idea.get("Video Type", "Short-form"))
        res["url"] = f"/api/audio/{idea_id}/{res['filename']}"
        return {"success": True, "audio": res}
    except Exception as e:
        message = str(e)
        status_code = 503 if "GEMINI_API_KEY is not configured" in message else 500
        raise HTTPException(status_code=status_code, detail=f"Voice synthesis failed: {message}")


@app.post("/api/video/render")
def render_video_endpoint(payload: Dict[str, Any] = Body(...)):
    """Renders scenes, visual prompts, and VoxArabic voiceover into ready-to-publish MP4."""
    idea_id = payload.get("idea_id")
    voice_key = payload.get("voice_key", "google_puck")
    is_vertical = payload.get("is_vertical", True)
    if not idea_id:
        raise HTTPException(status_code=400, detail="idea_id is required")

    try:
        res = video_engine.render_video_for_idea(
            idea_id=idea_id,
            voice_key=voice_key,
            is_vertical=is_vertical,
            video_type="Short-form" if is_vertical else "Long-form"
        )
        res["url"] = f"/api/video/{idea_id}/{res['filename']}"
        return {"success": True, "video": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video rendering failed: {str(e)}")


@app.post("/api/publishing/approve")
async def approve_and_dispatch(payload: Dict[str, Any] = Body(...)):
    """Approves publishing manifest for distribution across 5 platforms."""
    idea_id = payload.get("idea_id")
    approved = payload.get("approved", True)
    if not idea_id:
        raise HTTPException(status_code=400, detail="idea_id is required")
    if approved is not True:
        raise HTTPException(status_code=400, detail="Explicit approval is required.")

    # Fetch production package
    prod = await get_production_package(idea_id)
    if not prod.get("produced"):
        raise HTTPException(status_code=400, detail="Idea has not been produced yet. Generate assets first.")

    seo_data = prod.get("seo", {})
    thumbnails = prod.get("thumbnails", {})
    title = prod.get("metadata", {}).get("Video Title", "Untitled Video")

    thumb_data = {
        "youtube_path": thumbnails.get("youtube_path", ""),
        "vertical_path": thumbnails.get("vertical_path", "")
    }

    res = publishing_engine.prepare_publishing_manifest(
        idea_id, title, seo_data, thumb_data, approved=approved
    )

    if approved:
        idea_engine.update_idea_status(idea_id, "Approved / Scheduled")

    return res


@app.get("/api/analytics")
async def get_analytics_data():
    """Retrieves all analytics records, aggregations, and weekly digest."""
    records = analytics_engine.get_all_metrics()
    digest = analytics_engine.generate_weekly_telegram_digest()

    total_views = sum(int(float(r.get("Views", 0) or 0)) for r in records)
    total_likes = sum(int(float(r.get("Likes", 0) or 0)) for r in records)
    total_comments = sum(int(float(r.get("Comments", 0) or 0)) for r in records)
    total_shares = sum(int(float(r.get("Shares", 0) or 0)) for r in records)
    total_watch = sum(int(float(r.get("Watch Time (Mins)", 0) or 0)) for r in records)
    total_subs = sum(int(float(r.get("Subscribers Growth", 0) or 0)) for r in records)
    avg_ctr = round(sum(float(r.get("CTR (%)", 0) or 0) for r in records) / (len(records) or 1), 1)

    return {
        "records": records,
        "summary": {
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_watch_minutes": total_watch,
            "total_watch_hours": round(total_watch / 60, 1),
            "total_subscribers": total_subs,
            "avg_ctr": avg_ctr
        },
        "weekly_digest": digest
    }


@app.post("/api/analytics/refresh")
async def refresh_analytics():
    """Recalculates analytics and writes fresh weekly digest."""
    try:
        digest = analytics_engine.update_weekly_digest()
        return {"success": True, "digest": digest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
async def get_settings():
    """Reads settings from Settings.csv."""
    settings_dict = {}
    settings_path = DB_DIR / "Settings.csv"
    if settings_path.exists():
        with open(settings_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    settings_dict[row[0].strip()] = {
                        "value": row[1].strip(),
                        "description": row[2].strip() if len(row) > 2 else "",
                        "notes": row[3].strip() if len(row) > 3 else ""
                    }
    return settings_dict


@app.get("/api/auth/status")
async def auth_status():
    return {"required": bool(Config.APP_ADMIN_TOKEN)}


@app.post("/api/settings")
async def update_settings(payload: Dict[str, str] = Body(...)):
    """Updates settings in Settings.csv and applies to runtime Config."""
    settings_path = DB_DIR / "Settings.csv"
    if not settings_path.exists():
        raise HTTPException(status_code=404, detail="Settings.csv not found")

    rows = []
    with open(settings_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if row and row[0].strip() in payload:
                row[1] = payload[row[0].strip()]
            rows.append(row)

    with open(settings_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(rows)

    Config.load_from_settings_csv()
    return {"success": True, "message": "Settings updated successfully."}


@app.post("/api/pipeline/run-full-cycle")
async def run_full_automation_cycle():
    """Executes a full end-to-end automation test cycle."""
    if not Config.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="دورة الإنتاج متوقفة: أضف GEMINI_API_KEY إلى متغيرات Vercel ثم أعد النشر.",
        )
    try:
        # 1. Generate or fetch top idea
        ideas = idea_engine.get_all_ideas()
        candidate = next((i for i in reversed(ideas) if i.get("Status") == "New"), None)
        if not candidate:
            batch = idea_engine.generate_batch()
            idea_engine.save_ideas_to_database(batch)
            candidate = batch[0]
            idea_id = candidate["idea_id"]
        else:
            idea_id = candidate["Idea ID"]

        # 2. Run production
        prod_res = await generate_production_package({"idea_id": idea_id})

        # Analytics are collected only from real platform data, never synthetic demo values.
        digest = analytics_engine.update_weekly_digest()

        return {
            "success": True,
            "idea_id": idea_id,
            "title": candidate.get("Video Title", candidate.get("video_title", "")),
            "production": prod_res,
            "weekly_digest": digest
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Full production cycle failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="فشلت دورة الإنتاج. راجع سجل الخادم لمعرفة المرحلة المتسببة.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)
