"""
AI Content Factory - Scenario 8: Performance Analytics & Growth Intelligence
Tracks views, watch time, CTR, and subscriber growth; calculates algorithmic performance scores,
and formats executive Telegram digests with dynamic aggregation.
"""

import os
import sys
import json
import csv
import datetime
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config, DB_DIR, STORAGE_ROOT

class AnalyticsEngine:
    def __init__(self):
        self.analytics_csv = DB_DIR / "Analytics.csv"

    def record_metrics(self, record_data):
        """Logs performance record (Firestore when configured, else CSV)."""
        from core import firestore_store
        # Calculate algorithmic score (Retention & CTR weighted)
        views = float(record_data.get("views", 0))
        ctr = float(record_data.get("ctr", 0))
        likes = float(record_data.get("likes", 0))
        score = round((ctr * 0.4) + ((likes / (views or 1)) * 100 * 0.6), 2)
        score = min(score, 10.0)

        record_id = record_data.get("record_id", f"REC-{datetime.date.today().strftime('%Y%m%d')}")
        row_map = {
            "Record ID": record_id,
            "Idea ID": record_data.get("idea_id", "IDEA-001"),
            "Video Title": record_data.get("video_title", ""),
            "Platform": record_data.get("platform", "YouTube"),
            "Views": str(record_data.get("views", 0)),
            "Likes": str(record_data.get("likes", 0)),
            "Comments": str(record_data.get("comments", 0)),
            "Shares": str(record_data.get("shares", 0)),
            "Watch Time (Mins)": str(record_data.get("watch_time", 0)),
            "Average View Duration (AVD)": str(record_data.get("avd", "00:00")),
            "CTR (%)": str(record_data.get("ctr", 0)),
            "Subscribers Growth": str(record_data.get("subscribers_growth", 0)),
            "Recorded Date": datetime.date.today().isoformat(),
            "AI Performance Score": f"{score}/10",
        }

        if firestore_store.enabled():
            firestore_store.set_document("analytics", record_id, row_map, merge=True)
            return score

        headers = [
            "Record ID", "Idea ID", "Video Title", "Platform", "Views", "Likes",
            "Comments", "Shares", "Watch Time (Mins)", "Average View Duration (AVD)",
            "CTR (%)", "Subscribers Growth", "Recorded Date", "AI Performance Score"
        ]
        file_exists = self.analytics_csv.exists()

        existing_rows = []
        updated = False
        if file_exists:
            with open(self.analytics_csv, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if row and row[0] == record_id:
                        row = [row_map[h] for h in headers]
                        updated = True
                    if row:
                        existing_rows.append(row)

        with open(self.analytics_csv, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in existing_rows:
                writer.writerow(r)
            if not updated:
                writer.writerow([row_map[h] for h in headers])

        try:
            from database.generate_sheets_template import create_excel_workbook
            create_excel_workbook()
        except Exception as e:
            print(f"[!] Warning syncing Excel: {e}")

        return score

    def get_all_metrics(self):
        """Reads analytics records (Firestore when configured, else CSV)."""
        from core import firestore_store
        if firestore_store.enabled():
            records = firestore_store.get_records("analytics") or []
            # normalize keys for UI expectations
            return records
        records = []
        if not self.analytics_csv.exists():
            return records
        with open(self.analytics_csv, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records

    def generate_weekly_telegram_digest(self):
        """Analyzes analytics records dynamically and produces executive Arabic digest for Telegram."""
        records = self.get_all_metrics()
        
        if records:
            total_views = sum(int(float(r.get("Views", 0) or 0)) for r in records)
            total_likes = sum(int(float(r.get("Likes", 0) or 0)) for r in records)
            total_comments = sum(int(float(r.get("Comments", 0) or 0)) for r in records)
            total_shares = sum(int(float(r.get("Shares", 0) or 0)) for r in records)
            total_watch_time = sum(int(float(r.get("Watch Time (Mins)", 0) or 0)) for r in records)
            total_subs = sum(int(float(r.get("Subscribers Growth", 0) or 0)) for r in records)
            avg_ctr = round(sum(float(r.get("CTR (%)", 0) or 0) for r in records) / len(records), 1)
            
            # Sort by Views descending
            sorted_by_views = sorted(records, key=lambda x: float(x.get("Views", 0) or 0), reverse=True)
            top_videos_lines = []
            for idx, vid in enumerate(sorted_by_views[:3], start=1):
                title = vid.get("Video Title", "فيديو بدون عنوان")
                platform = vid.get("Platform", "YouTube")
                views = int(float(vid.get("Views", 0) or 0))
                ctr = vid.get("CTR (%)", "0")
                score = vid.get("AI Performance Score", "—")
                top_videos_lines.append(
                    f"{idx}. <i>'{title}'</i> ({platform})\n"
                    f"   👁️ <b>{views:,}</b> مشاهدة | 🎯 CTR: <b>{ctr}%</b> | ⭐ تقييم: <b>{score}</b>"
                )
            top_videos_formatted = "\n".join(top_videos_lines)
        else:
            return "لا توجد بيانات أداء فعلية حتى الآن. أضف سجلات من مصدر موثوق لعرض التقرير الأسبوعي."

        hours_watch_time = total_watch_time // 60 if total_watch_time >= 60 else total_watch_time

        report = (
            "📊 <b>التقرير الأسبوعي لأداء مصنع المحتوى (Weekly Growth Digest):</b>\n\n"
            "📈 <b>أرقام الأسبوع الإجمالية:</b>\n"
            f"• إجمالي المشاهدات: <b>{total_views:,}</b> مشاهدة\n"
            f"• إجمالي وقت المشاهدة: <b>{total_watch_time:,}</b> دقيقة (~{hours_watch_time:,} ساعة)\n"
            f"• متوسط نسبة النقر للظهور (CTR): <b>{avg_ctr}%</b>\n"
            f"• المشتركون الجدد: <b>+{total_subs:,}</b> مشترك\n"
            f"• إجمالي التفاعل: <b>{total_likes:,}</b> إعجاب | <b>{total_comments:,}</b> تعليق | <b>{total_shares:,}</b> مشاركة\n\n"
            "🏆 <b>أفضل الفيديوهات أداءً هذا الأسبوع:</b>\n"
            f"{top_videos_formatted}\n\n"
            "💡 <b>ملحوظة:</b> المؤشرات محسوبة من السجلات المسجلة فقط. اربط مصدر التحليلات لتوسيع التقرير."
        )

        # Save to markdown files for persistent access
        try:
            STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
            storage_digest_path = STORAGE_ROOT / "weekly_analytics_digest.md"
            db_digest_path = DB_DIR / "weekly_analytics_digest.md"

            md_content = f"# {report.replace('<b>', '**').replace('</b>', '**').replace('<i>', '*').replace('</i>', '*')}"
            
            with open(storage_digest_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            with open(db_digest_path, "w", encoding="utf-8") as f:
                f.write(md_content)
        except Exception as e:
            print(f"[!] Warning saving digest file: {e}")

        return report

    def update_weekly_digest(self):
        """Generates and saves the weekly analytics digest."""
        digest = self.generate_weekly_telegram_digest()
        print("[✓] Weekly analytics digest updated successfully.")
        return digest

if __name__ == "__main__":
    engine = AnalyticsEngine()
    digest = engine.update_weekly_digest()
    print("\n" + "=" * 60)
    print(digest)
    print("=" * 60)
