"""
AI Content Factory - Scenario 6: Storage Engine & Directory Orchestrator
Manages local and Google Drive folder hierarchies under:
/AI Content Factory/2026/Video_ID/
  /Research
  /Scripts
  /SEO
  /Thumbnails
  /Video_Assets
  /Publishing
"""

import os
import json
import mimetypes
from pathlib import Path
from core.config import STORAGE_ROOT

class StorageEngine:
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else STORAGE_ROOT
        self.subfolders = [
            "Research", "Scripts", "SEO", "Thumbnails", "Video_Assets", "Publishing"
        ]

    def create_video_structure(self, idea_id):
        """Creates the full 6-directory tree for a video."""
        video_dir = self.root_dir / idea_id
        folder_paths = {}
        for sub in self.subfolders:
            sub_path = video_dir / sub
            sub_path.mkdir(parents=True, exist_ok=True)
            folder_paths[sub] = str(sub_path)
            
        return {
            "idea_id": idea_id,
            "root_video_dir": str(video_dir),
            "subfolders": folder_paths
        }

    def save_script_asset(self, idea_id, script_data):
        """Saves script markdown and scene breakdown JSON to /Scripts."""
        paths = self.create_video_structure(idea_id)["subfolders"]
        scripts_dir = Path(paths["Scripts"])
        
        md_file = scripts_dir / f"{script_data['script_id']}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# Script: {script_data['idea_id']} ({script_data['video_type']})\n\n")
            f.write(f"**Duration:** {script_data['estimated_duration']} | **Word Count:** {script_data['word_count']}\n\n")
            f.write(f"## Hook (0-3s):\n{script_data['hook_3s']}\n\n")
            f.write(f"## Full Voiceover:\n{script_data['full_voiceover']}\n\n")
            f.write(f"## CTA:\n{script_data['cta']}\n")
            
        json_file = scripts_dir / f"scenes_{script_data['script_id']}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(script_data["scene_breakdown"], f, ensure_ascii=False, indent=2)
            
        return str(md_file), str(json_file)

    def sync_to_cloud(self, idea_id):
        """Upload generated assets to configured cloud file storage (Firebase Storage or R2)."""
        root = self.root_dir / idea_id
        providers = []
        # Prefer Firebase Storage when configured (fits "Firestore/Firebase only" setups)
        try:
            from core import firebase_storage
            if firebase_storage.enabled():
                providers.append(("Firebase Storage", firebase_storage))
        except Exception:
            pass
        try:
            from core import r2_storage
            if r2_storage.enabled():
                providers.append(("Cloudflare R2", r2_storage))
        except Exception:
            pass
        try:
            from core import cloudinary_storage
            if cloudinary_storage.enabled():
                providers.append(("Cloudinary", cloudinary_storage))
        except Exception:
            pass
        if not providers:
            return {"uploaded": 0, "configured": False, "provider": "local files (temporary on Vercel)"}

        uploaded = 0
        errors = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            object_key = f"{idea_id}/{relative}"
            ok = False
            for name, mod in providers:
                try:
                    mod.put_file(path, object_key, content_type)
                    ok = True
                    break
                except Exception as e:
                    errors.append(f"{name}: {e}")
            if ok:
                uploaded += 1
        res = {"uploaded": uploaded, "configured": True, "provider": ", ".join([p[0] for p in providers])}
        if errors and uploaded == 0:
            res["error"] = errors[-1]
        return res

    def sync_to_r2(self, idea_id):
        """Backward-compatible alias."""
        return self.sync_to_cloud(idea_id)

    def save_seo_asset(self, idea_id, seo_data):
        """Saves SEO metadata JSON and copyable text file to /SEO."""
        paths = self.create_video_structure(idea_id)["subfolders"]
        seo_dir = Path(paths["SEO"])
        
        json_file = seo_dir / f"{seo_data['seo_id']}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(seo_data, f, ensure_ascii=False, indent=2)
            
        txt_file = seo_dir / f"copyable_metadata_{idea_id}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"=== BEST TITLE ===\n{seo_data['recommended_best_title']}\n\n")
            f.write(f"=== ALTERNATIVE TITLES ===\n" + "\n".join(seo_data['alternative_titles']) + "\n\n")
            f.write(f"=== YOUTUBE DESCRIPTION ===\n{seo_data['youtube_description']}\n\n")
            f.write(f"=== SHORT DESCRIPTION (REELS / TIKTOK) ===\n{seo_data['short_description_reels_tiktok']}\n\n")
            f.write(f"=== TAGS (20) ===\n" + ", ".join(seo_data['tags_20']) + "\n\n")
            f.write(f"=== HASHTAGS (5) ===\n" + " ".join(seo_data['hashtags_5']) + "\n\n")
            f.write(f"=== PINNED COMMENT ===\n{seo_data['pinned_comment']}\n")
            
        return str(json_file), str(txt_file)
