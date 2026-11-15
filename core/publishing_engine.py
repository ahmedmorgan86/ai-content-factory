"""
AI Content Factory - Scenario 7: Multi-Platform Publishing Dispatcher
Prepares distribution payloads for YouTube, YouTube Shorts, TikTok, Instagram Reels, and Facebook Reels.
Enforces safety rule: Never publish without user approval.
"""

import os
import json
import csv
import datetime
from pathlib import Path
from core.config import Config, DB_DIR

class PublishingEngine:
    def __init__(self):
        self.publishing_csv = DB_DIR / "Publishing.csv"

    def prepare_publishing_manifest(self, idea_id, title, seo_data, thumb_data, approved=False):
        """
        Creates platform-specific publishing payloads with safety verification.
        """
        if not approved:
            return {
                "status": "BLOCKED_APPROVAL_REQUIRED",
                "message": "Security policy enforced: Cannot schedule or publish without explicit user approval."
            }

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        platforms_payload = [
            {
                "platform": "YouTube",
                "mode": "API Scheduled / Draft",
                "title": seo_data.get("recommended_best_title", title)[:100],
                "description": seo_data.get("youtube_description", ""),
                "tags": seo_data.get("tags_20", []),
                "thumbnail": thumb_data.get("youtube_path", ""),
                "privacy": "private",
                "status": "Ready for API Dispatch / Review"
            },
            {
                "platform": "YouTube Shorts",
                "mode": "API Scheduled / Draft",
                "title": seo_data.get("recommended_best_title", title)[:90] + " #Shorts",
                "description": seo_data.get("short_description_reels_tiktok", ""),
                "tags": seo_data.get("tags_20", []),
                "thumbnail": thumb_data.get("vertical_path", ""),
                "privacy": "private",
                "status": "Ready for API Dispatch / Review"
            },
            {
                "platform": "TikTok",
                "mode": "Official Content Posting API / Manual Packager",
                "caption": seo_data.get("short_description_reels_tiktok", "")[:150],
                "hashtags": seo_data.get("hashtags_5", []),
                "cover_image": thumb_data.get("vertical_path", ""),
                "status": "Ready for Dispatch"
            },
            {
                "platform": "Instagram Reels",
                "mode": "Instagram Graph API / Manual Packager",
                "caption": seo_data.get("short_description_reels_tiktok", ""),
                "hashtags": seo_data.get("hashtags_5", []),
                "cover_image": thumb_data.get("vertical_path", ""),
                "status": "Ready for Dispatch"
            },
            {
                "platform": "Facebook Reels",
                "mode": "Meta Pages API / Manual Packager",
                "caption": seo_data.get("short_description_reels_tiktok", ""),
                "hashtags": seo_data.get("hashtags_5", []),
                "cover_image": thumb_data.get("vertical_path", ""),
                "status": "Ready for Dispatch"
            }
        ]

        # Record to Publishing.csv
        file_exists = self.publishing_csv.exists()
        headers = [
            "Publish ID", "Idea ID", "Video Title", "Platform", "Scheduled Date", 
            "Published Date", "Post URL", "Publishing Mode", "User Approval Status", 
            "Execution Log", "Last Status Check"
        ]

        with open(self.publishing_csv, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            for p in platforms_payload:
                publish_id = f"PUB-{idea_id}-{p['platform'].replace(' ', '_')}"
                writer.writerow([
                    publish_id,
                    idea_id,
                    p.get("title", title),
                    p["platform"],
                    now_str,
                    "-",
                    "-",
                    p["mode"],
                    "Approved by Admin",
                    "Payload prepared and validated",
                    now_str
                ])

        return {
            "status": "SUCCESS_PREPARED",
            "idea_id": idea_id,
            "manifest": platforms_payload
        }
