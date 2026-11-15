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

app = FastAPI(
    title="AI Content Factory Command Center",
    description="Autonomous Content Engine Dashboard & Controller",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    target = STORAGE_ROOT / idea_id / "Thumbnails" / filename
    if target.exists() and target.is_file():
        return FileResponse(target)
    fallback = BASE_DIR / "storage" / "AI Content Factory" / "2026" / idea_id / "Thumbnails" / filename
    if fallback.exists() and fallback.is_file():
        return FileResponse(fallback)
    raise HTTPException(status_code=404, detail="Thumbnail not found")

@app.get("/storage/{file_path:path}")
async def serve_storage_file(file_path: str):
    """Serves files from storage safely across local and Vercel environments."""
    from core.config import IS_VERCEL
    if IS_VERCEL:
        tmp_target = Path("/tmp/ai-content-factory/storage") / file_path
        if tmp_target.exists() and tmp_target.is_file():
            return FileResponse(tmp_target)
    local_target = (BASE_DIR / "storage") / file_path
    if local_target.exists() and local_target.is_file():
        return FileResponse(local_target)
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
        return HTMLResponse(content=f.read())


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

    return {
        "status": "online",
        "system_time": "2026-11-15T21:42:00+02:00",
        "kpis": {
            "total_ideas": total_ideas,
            "short_ideas": short_count,
            "long_ideas": long_count,
            "ready_packages": ready_count,
            "total_views": total_views,
            "total_watch_hours": round(total_watch / 60, 1),
            "total_subscribers": total_subs,
            "avg_ctr": avg_ctr
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
        "publishing": publishing_records,
        "storage_path": str(video_dir)
    }


@app.post("/api/production/generate")
async def generate_production_package(payload: Dict[str, Any] = Body(...)):
    """Runs complete production generation (Scripts, SEO, Thumbnails, Storage, Publishing manifest)."""
    idea_id = payload.get("idea_id")
    if not idea_id:
        raise HTTPException(status_code=400, detail="idea_id is required")

    ideas = idea_engine.get_all_ideas()
    selected_idea = next((i for i in ideas if i.get("Idea ID") == idea_id), None)
    if not selected_idea:
        raise HTTPException(status_code=404, detail=f"Idea {idea_id} not found in database")

    # Map database row format to engine format
    idea_dict = {
        "idea_id": selected_idea.get("Idea ID"),
        "video_title": selected_idea.get("Video Title"),
        "video_summary": selected_idea.get("Video Summary"),
        "target_audience": selected_idea.get("Target Audience"),
        "hook": selected_idea.get("Hook"),
        "content_angle": selected_idea.get("Content Angle"),
        "video_type": selected_idea.get("Video Type", "Short-form"),
        "estimated_duration": selected_idea.get("Estimated Duration", "60 ثانية"),
        "seo_keywords": [k.strip() for k in selected_idea.get("SEO Keywords", "").split(",") if k.strip()]
    }

    try:
        # 1. Scripts
        short_script = script_engine.generate_short_script(idea_dict)
        long_script = script_engine.generate_long_script(idea_dict)
        script_to_use = short_script if "Short" in idea_dict["video_type"] else long_script
        script_engine.save_script_to_database(script_to_use)

        # 2. SEO Package
        seo_pkg = seo_engine.generate_seo_package(idea_dict, script_to_use)
        seo_engine.save_seo_to_database(seo_pkg)

        # 3. Create Storage Structure & stage scripts/SEO
        storage_engine.create_video_structure(idea_id)
        storage_engine.save_script_asset(idea_id, script_to_use)
        storage_engine.save_seo_asset(idea_id, seo_pkg)

        # 4. Generate & Verify Thumbnails (1280x720 & 1080x1920)
        target_thumb_dir = STORAGE_ROOT / idea_id / "Thumbnails"
        thumb_res = thumbnail_engine.generate_and_verify_thumbnails(
            idea_id, idea_dict["video_title"], output_dir=target_thumb_dir
        )

        # 5. Prepare Publishing Manifest (Unapproved / Pending by default)
        publishing_engine.prepare_publishing_manifest(
            idea_id, idea_dict["video_title"], seo_pkg, thumb_res, approved=False
        )

        # 6. Update status in Ideas.csv
        idea_engine.update_idea_status(idea_id, "Ready for Production")

        return {
            "success": True,
            "idea_id": idea_id,
            "message": "Full production package generated and verified successfully.",
            "script": script_to_use,
            "seo": seo_pkg,
            "thumbnails": thumb_res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/publishing/approve")
async def approve_and_dispatch(payload: Dict[str, Any] = Body(...)):
    """Approves publishing manifest for distribution across 5 platforms."""
    idea_id = payload.get("idea_id")
    approved = payload.get("approved", True)
    if not idea_id:
        raise HTTPException(status_code=400, detail="idea_id is required")

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

        # 3. Log analytics
        rec_id = f"REC-{idea_id}"
        analytics_engine.record_metrics({
            "record_id": rec_id,
            "idea_id": idea_id,
            "video_title": candidate.get("Video Title", candidate.get("video_title", "")),
            "platform": "YouTube",
            "views": 42000,
            "likes": 3100,
            "comments": 220,
            "shares": 540,
            "watch_time": 210000,
            "avd": "05:30",
            "ctr": 12.1,
            "subscribers_growth": 740
        })

        # 4. Refresh digest
        digest = analytics_engine.update_weekly_digest()

        return {
            "success": True,
            "idea_id": idea_id,
            "title": candidate.get("Video Title", candidate.get("video_title", "")),
            "production": prod_res,
            "weekly_digest": digest
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)
