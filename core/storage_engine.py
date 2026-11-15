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
