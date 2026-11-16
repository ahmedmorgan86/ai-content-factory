"""
AI Content Factory - Scenario 4: SEO & Metadata Package Generator
Generates 5 alternative titles, best title, platform-tailored descriptions, 20 tags, 5 hashtags, and pinned comment.
"""

import os
import json
import csv
from pathlib import Path
from core.config import Config, DB_DIR

class SEOEngine:
    def __init__(self):
        self.seo_csv = DB_DIR / "SEO.csv"

    def generate_seo_package(self, idea, script_data):
        """Generates comprehensive SEO and distribution metadata."""
        idea_id = idea.get("idea_id", "IDEA-001")
        title = idea.get("video_title", "")
        video_type = script_data.get("video_type", "Long-form")
        
        alt_titles = [
            f"إزاي تستخدم وكلاء الذكاء الاصطناعي (AI Agents) في أتمتة شغلك في 2026؟",
            f"ابني موظفك الرقمي بنفسك: دليل وكلاء الـ AI للمبتدئين خطوة بخطوة!",
            f"ليه كل الشركات بتتحول لـ AI Agents دلوقتي؟ (الشرح العملي الكامل)",
            f"أكبر خطأ بيقع فيه مستخدمو الذكاء الاصطناعي.. وازاي تصلحه بالـ Agents؟",
            f"وفرت 20 ساعة عمل أسبوعياً بالحركة دي في الذكاء الاصطناعي!"
        ]
        best_title = alt_titles[0]
        
        youtube_desc = (
            f"في هذا الفيديو، نستعرض دليلاً عملياً وشاملاً لشرح ثورة وكلاء الذكاء الاصطناعي (AI Agents) لعام 2026. "
            f"سنتعلم معاً كيفية بناء وكيل ذكي مستقل يقوم بإنجاز مهامك اليومية وأتمتة العمل الروتيني بكفاءة وسرعة فائقة.\n\n"
            f"⏱️ الفصول الزمنية (Timestamps):\n"
            f"00:00 - المقدمة والخطاف الصادم\n"
            f"01:45 - إيه هو الـ AI Agent وليه بيفرق عن الشات التقليدي؟\n"
            f"04:15 - التجربة العملية وبناء الوكيل خطوة بخطوة\n"
            f"07:30 - أسرار تفادي الأخطاء ومستقبل الوظائف\n"
            f"09:30 - الخاتمة والخطوات التالية\n\n"
            f"🔗 روابط الأدوات والقوالب المذكورة:\n"
            f"- رابط قالب الأتمتة المفتوح: https://github.com/ai-content-factory/templates\n"
            f"- مجتمعنا التقني على تليجرام: https://t.me/ai_content_factory_hub\n\n"
            f"📌 الكلمات المفتاحية الرئيسية:\n"
            f"#ذكاء_اصطناعي #تكنولوجيا #AI_Agents #أتمتة_المهام #مستقبل_العمل"
        )
        
        short_desc = (
            f"إزاي تبني موظف ذكاء اصطناعي يشتغل بدالك 24 ساعة ببلاش؟ 🤖⚡ "
            f"شوف الفيديو للآخر واكتبلي كلمة 'وكيل' في التعليقات عشان أبعتلك القالب مجاناً! "
            f"#ذكاء_اصطناعي #تقنية #AI #أتمتة #شورتس"
        )
        
        tags_20 = [
            "ذكاء اصطناعي", "AI 2026", "وكلاء الذكاء الاصطناعي", "AI Agents", 
            "أتمتة الأعمال", "تعلم الذكاء الاصطناعي", "Make automation", "n8n", 
            "ChatGPT 2026", "OpenAI", "أدوات تقنية", "برمجة بدون كود", 
            "No Code AI", "إنتاجية", "مستقبل التكنولوجيا", "تطوير الذات", 
            "تطبيقات الذكاء الاصطناعي في مصر", "أدوات مجانية", "Prompt Engineering", "تقنية عربية"
        ]
        
        hashtags_5 = [
            "#ذكاء_اصطناعي", "#تكنولوجيا", "#AI_Tools", "#أتمتة", "#FutureTech"
        ]
        
        primary_kws = ["ذكاء اصطناعي", "وكلاء الذكاء الاصطناعي", "AI Agents 2026"]
        secondary_kws = ["أتمتة المهام", "أدوات إنتاجية مجانية", "دليل الذكاء الاصطناعي العملي"]
        
        pinned_comment = (
            "🚀 كل الأدوات والقوالب المشروحة في الفيديو متاحة مجاناً في الرابط ده: "
            "[https://bit.ly/ai-agents-2026-guide] \n\n"
            "سؤال الحلقة: إيه أكتر مهمة مملة في يومك نفسك تبرمج AI Agent يعملها بدالك؟ "
            "اكتبهالي في التعليقات وهختار فكرة أطبقها في الفيديو الجاي! 👇"
        )
        
        related_ideas = [
            "أفضل 5 منصات لبناء البوتات والوكلاء بدون كود",
            "مقارنة بين تكلفة تشغيل AI Agent محلياً وعلى السحابة"
        ]
        
        return {
            "seo_id": f"SEO-{idea_id}",
            "idea_id": idea_id,
            "recommended_best_title": best_title,
            "alternative_titles": alt_titles,
            "youtube_description": youtube_desc,
            "short_description_reels_tiktok": short_desc,
            "tags_20": tags_20,
            "hashtags_5": hashtags_5,
            "primary_keywords": primary_kws,
            "secondary_keywords": secondary_kws,
            "pinned_comment": pinned_comment,
            "related_video_ideas": related_ideas
        }

    def save_seo_to_database(self, seo_data):
        """Saves SEO record (Firestore when configured, else CSV)."""
        from core import firestore_store
        row = {
            "SEO ID": seo_data["seo_id"],
            "Idea ID": seo_data["idea_id"],
            "Main Title": seo_data["recommended_best_title"],
            "Alternative Title 1": seo_data["alternative_titles"][0],
            "Alternative Title 2": seo_data["alternative_titles"][1],
            "Alternative Title 3": seo_data["alternative_titles"][2],
            "Alternative Title 4": seo_data["alternative_titles"][3],
            "Alternative Title 5": seo_data["alternative_titles"][4],
            "YouTube Description": seo_data["youtube_description"],
            "Short Description (Reels/TikTok)": seo_data["short_description_reels_tiktok"],
            "Tags (Comma-separated)": ", ".join(seo_data["tags_20"]),
            "Hashtags": " ".join(seo_data["hashtags_5"]),
            "Primary Keywords": ", ".join(seo_data["primary_keywords"]),
            "Secondary Keywords": ", ".join(seo_data["secondary_keywords"]),
            "Pinned Comment": seo_data["pinned_comment"],
            "Related Video Ideas": ", ".join(seo_data["related_video_ideas"]),
        }
        if firestore_store.enabled():
            firestore_store.set_document("seo", seo_data["seo_id"], row, merge=True)
            return seo_data["seo_id"]

        headers = list(row.keys())
        file_exists = self.seo_csv.exists()
        with open(self.seo_csv, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow([row[h] for h in headers])
        return seo_data["seo_id"]
