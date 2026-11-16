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
                "mode": "Manual upload / Draft",
                "title": seo_data.get("recommended_best_title", title)[:100],
                "description": seo_data.get("youtube_description", ""),
                "tags": seo_data.get("tags_20", []),
                "thumbnail": thumb_data.get("youtube_path", ""),
                "privacy": "private",
                "status": "Ready for API Dispatch / Review"
            },
            {
                "platform": "YouTube Shorts",
                "mode": "Manual upload / Draft",
                "title": seo_data.get("recommended_best_title", title)[:90] + " #Shorts",
                "description": seo_data.get("short_description_reels_tiktok", ""),
                "tags": seo_data.get("tags_20", []),
                "thumbnail": thumb_data.get("vertical_path", ""),
                "privacy": "private",
                "status": "Ready for API Dispatch / Review"
            },
            {
                "platform": "TikTok",
                "mode": "Manual upload / Content packager",
                "caption": seo_data.get("short_description_reels_tiktok", "")[:150],
                "hashtags": seo_data.get("hashtags_5", []),
                "cover_image": thumb_data.get("vertical_path", ""),
                "status": "Ready for Dispatch"
            },
            {
                "platform": "Instagram Reels",
                "mode": "Manual upload / Content packager",
                "caption": seo_data.get("short_description_reels_tiktok", ""),
                "hashtags": seo_data.get("hashtags_5", []),
                "cover_image": thumb_data.get("vertical_path", ""),
                "status": "Ready for Dispatch"
            },
            {
                "platform": "Facebook Reels",
                "mode": "Manual upload / Content packager",
                "caption": seo_data.get("short_description_reels_tiktok", ""),
                "hashtags": seo_data.get("hashtags_5", []),
                "cover_image": thumb_data.get("vertical_path", ""),
                "status": "Ready for Dispatch"
            }
        ]

        # Record publishing manifest (Firestore when configured, else CSV)
        from core import firestore_store
        headers = [
            "Publish ID", "Idea ID", "Video Title", "Platform", "Prepared Date",
            "Published Date", "Post URL", "Publishing Mode", "User Approval Status",
            "Execution Log", "Last Status Check"
        ]

        rows_to_write = []
        for p in platforms_payload:
            publish_id = f"PUB-{idea_id}-{p['platform'].replace(' ', '_')}"
            row = {
                "Publish ID": publish_id,
                "Idea ID": idea_id,
                "Video Title": p.get("title", title),
                "Platform": p["platform"],
                "Prepared Date": now_str,
                "Published Date": "-",
                "Post URL": "-",
                "Publishing Mode": p["mode"],
                "User Approval Status": "Approved for manual publishing",
                "Execution Log": "Payload prepared and validated",
                "Last Status Check": now_str,
            }
            rows_to_write.append(row)

        if firestore_store.enabled():
            for row in rows_to_write:
                firestore_store.set_document("publishing", row["Publish ID"], row, merge=True)
        else:
            file_exists = self.publishing_csv.exists()
            with open(self.publishing_csv, mode="a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(headers)
                for row in rows_to_write:
                    writer.writerow([row[h] for h in headers])

        return {
            "status": "SUCCESS_PREPARED",
            "message": "تم إعداد بيانات النشر للمراجعة. لا يوجد نشر مباشر؛ اربط حساب المنصة لإتمامه.",
            "idea_id": idea_id,
            "manifest": platforms_payload
        }
