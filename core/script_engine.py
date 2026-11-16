"""
AI Content Factory - Scenario 2 & 3: Script & Scene Breakdown Engine
Generates Egyptian Arabic scripts (Short & Long) with full 8-point cinematic Scene Breakdowns.
"""

import os
import json
import csv
from pathlib import Path
from core.config import Config, DB_DIR

class ScriptEngine:
    def __init__(self):
        self.scripts_csv = DB_DIR / "Scripts.csv"

    def generate_short_script(self, idea):
        """Generates a high-retention 45-60s Short-form script with scene breakdown."""
        title = idea.get("video_title", "")
        idea_id = idea.get("idea_id", "IDEA-001")
        
        hook = idea.get("hook", "تخيل لو عندك موظف شاطر جداً بيشتغل 24 ساعة ببلاش ومابيشتكيش!")
        
        voiceover_text = (
            f"{hook} "
            "الموضوع مش خيال ولا كلام تسويق.. في 2026 ظهرت أدوات وكلاء ذكاء اصطناعي (AI Agents) "
            "بتقدر تديهم مهمة واحدة معقدة، وهما يقسموها وينفذوها لوحدهم! "
            "يعني بدل ما تقعد 3 ساعات ترد على إيميلات العملاء وتنسق المواعيد، "
            "أنت بتعمل Agent صغير على أدوات زي Make أو n8n، وهو بيتولى اللعبة كلها بدقة متناهية. "
            "السر كله إنك تبدأ بحاجة بسيطة وتفهم إزاي توجهه بالـ Prompts الصح. "
            "لو عايزني أعملك شرح تطبيقي خطوة بخطوة إزاي تبني أول Agent ليك، "
            "اكتبلي كلمة 'وكيل' في التعليقات واعمل فولو عشان الفيديو الجاي هيفوتك كتير!"
        )
        
        words = len(voiceover_text.split())
        est_duration = f"{int(words / 2.3)} ثانية"
        
        scenes = [
            {
                "scene_number": 1,
                "timecode": "00:00 - 00:04",
                "duration_seconds": 4,
                "voiceover": hook,
                "visual_description": "لقطة مقربة وسريعة لوجه المتحدث بتعبير دهشة وتحدٍ، مع تأثير زووم سريع (Speed Ramp).",
                "b_roll": "شاشات كود ثلاثية الأبعاد وواجهات برمجية تدور حول المتحدث في غرفة مضاءة بنيون أزرق.",
                "on_screen_text": "موظف 24 ساعة ببلاش؟! 🤖",
                "sfx": "Fast cinematic whoosh + Deep sub-impact",
                "ai_video_prompt": "Cinematic portrait shot of an energetic young tech specialist looking surprised into the camera, neon electric blue lighting, dynamic zoom, 8k photorealistic."
            },
            {
                "scene_number": 2,
                "timecode": "00:04 - 00:15",
                "duration_seconds": 11,
                "voiceover": "الموضوع مش خيال ولا كلام تسويق.. في 2026 ظهرت أدوات وكلاء ذكاء اصطناعي بتقدر تديهم مهمة واحدة معقدة وهما ينفذوها لوحدهم!",
                "visual_description": "انتقال سريع للشاشة يستعرض واجهة وكيل ذكاء اصطناعي وهو ينجز 4 مهام في ثوانٍ متتالية.",
                "b_roll": "تصوير سريع للشاشة (Screen Recording) لواجهة سير عمل مؤتمتة تسجل ردود وإيميلات تلقائياً.",
                "on_screen_text": "ثورة AI Agents ⚡",
                "sfx": "Rapid mouse clicking + Cyber interface glitches",
                "ai_video_prompt": "Futuristic UI HUD interface showing automated AI agent executing multiple tasks simultaneously, floating nodes and glowing data packets, 4k 60fps."
            },
            {
                "scene_number": 3,
                "timecode": "00:15 - 00:35",
                "duration_seconds": 20,
                "voiceover": "يعني بدل ما تقعد 3 ساعات ترد على إيميلات العملاء وتنسق المواعيد، أنت بتعمل Agent صغير وهو بيتولى اللعبة كلها بدقة متناهية. السر كله إنك تبدأ بحاجة بسيطة وتفهم إزاي توجهه بالـ Prompts الصح.",
                "visual_description": "المتحدث يعود للكادر حاملاً هاتفه الذكي مشيراً إلى سلاسة وسرعة وصول الإشعارات التلقائية.",
                "b_roll": "رسم بياني حركي (Motion Graphics) يوضح توفير 15 ساعة عمل أسبوعياً.",
                "on_screen_text": "وفّر 15 ساعة أسبوعياً! ⏳",
                "sfx": "Clock ticking speeding up then cash register bell 'Ching!'",
                "ai_video_prompt": "Minimalist sleek 3D motion graphic animation of a digital clock transforming into glowing energy sparks, dark slate background."
            },
            {
                "scene_number": 4,
                "timecode": "00:35 - 00:50",
                "duration_seconds": 15,
                "voiceover": "لو عايزني أعملك شرح تطبيقي خطوة بخطوة إزاي تبني أول Agent ليك، اكتبلي كلمة 'وكيل' في التعليقات واعمل فولو عشان الفيديو الجاي هيفوتك كتير!",
                "visual_description": "سهم حركي يوجه المشاهد إلى زر المتابعة وصندوق التعليقات مع وميض أنيق للوجو القناة.",
                "b_roll": "أيقونة تعليق وزر فولو ثلاثي الأبعاد مضيء باللون السماوي يرتد بسلاسة.",
                "on_screen_text": "اكتب 'وكيل' في التعليقات 👇",
                "sfx": "Pop sound effect + Smooth whoosh exit",
                "ai_video_prompt": "Glowing 3D notification icon floating smoothly with modern tech particle ambiance, soft studio lighting."
            }
        ]
        
        return {
            "script_id": f"SCR-SHORT-{idea_id}",
            "idea_id": idea_id,
            "video_type": "Short-form",
            "language": "Egyptian Arabic",
            "hook_3s": hook,
            "full_voiceover": voiceover_text,
            "scene_breakdown": scenes,
            "cta": "اكتبلي كلمة 'وكيل' في التعليقات واعمل فولو عشان الفيديو الجاي!",
            "word_count": words,
            "estimated_duration": est_duration,
            "status": "Ready for Production"
        }

    def generate_long_script(self, idea):
        """Generates a structured, engaging 8-10m Long-form script with chapter breakdown."""
        title = idea.get("video_title", "")
        idea_id = idea.get("idea_id", "IDEA-001")
        
        hook = idea.get("hook", "تخيل لو عندك موظف شاطر جداً بيشتغل 24 ساعة ببلاش ومابيشتكيش!")
        
        chapters = [
            {
                "chapter_index": 1,
                "timestamp": "00:00",
                "title": "المقدمة والخطاف الصادم (The Hook & Promise)",
                "voiceover": (
                    f"{hook} "
                    "أهلاً بيك يا صديقي في حلقة جديدة من مصنع المحتوى الذكي. "
                    "النهاردة إحنا مش جايين نتكلم عن شات جي بي تي العادي اللي بتسأله سؤال ويرد عليك.. "
                    "النهاردة إحنا بنتكلم عن النقلة الكبرى في عالم الذكاء الاصطناعي: وكلاء الـ AI المستقلين (Autonomous Agents). "
                    "في نهاية الفيديو ده، هتكون عارف بالضبط إيه هما، وبيشتغلوا إزاي، والأهم من كده: "
                    "هنبني سوا خطوة بخطوة وكيل عملي يخدمك في شغلك أو دراستك بدون أي تعقيد برمجي. "
                    "جهز فنجان قهوتك المظبوط، وركز معايا كويس جداً لأن الدقايق دي هتغير نظرتك لإنتاجيتك بالكامل."
                )
            },
            {
                "chapter_index": 2,
                "timestamp": "01:45",
                "title": "الفصل الأول: إيه هو الـ AI Agent وليه بيفرق عن الشات التقليدي؟",
                "voiceover": (
                    "عشان تفهم الفكرة ببساطة شديدة: الشات بوت العادي عامل زي الموظف اللي مستنيك تقوله اعمل كذا، "
                    "ولو سكتت هو مش هيعمل أي حاجة. "
                    "لكن الـ Agent هو الموظف المبتكر اللي بتديله الهدف النهائي، وهو اللي بيحط الخطة لنفسه! "
                    "يعني بتقوله: 'أنا عاوزك تجهزلي تقرير عن أفضل 5 أدوات ذكاء اصطناعي نزلت الأسبوع ده'. "
                    "الوكيل بيروح لوحده يفتح الإنترنت، يدور في المصادر، يفلتر المعلومات، "
                    "يكتب التقرير، ويبعتهولك في إيميل منسق وجاهز. "
                    "هو بيمتلك 3 حاجات أساسية: الذاكرة (Memory)، الأدوات (Tools)، والقدرة على التفكير واتخاذ القرار (Reasoning)."
                )
            },
            {
                "chapter_index": 3,
                "timestamp": "04:15",
                "title": "الفصل الثاني: البناء العملي وتجربة الأدوات على الهواء",
                "voiceover": (
                    "تعال بقى نفتح الشاشة ونشوف التطبيق العملي. "
                    "هنستخدم منصة أوتوميشن ذكية زي Make أو n8n مع ربطها بـ OpenAI API. "
                    "الخطوة الأولى: تحديد المدخلات (Trigger) وليكن رسالة بتوصلنا على تليجرام. "
                    "الخطوة الثانية: الـ Reasoning Module، وهنا بنكتب برومبت دقيق بيوجه الموديل إنه يحلل الطلب ويقسمه. "
                    "الخطوة الثالثة: التنفيذ (Action)، وهنا بنربطه بأدوات بحث وتخزين زي Google Sheets. "
                    "بص على الشاشة هنا.. بمجرد ما بعتنا الأمر، الوكيل بدأ يشتغل، وخلال 15 ثانية كانت المهمة خلصانة بنجاح 100%!"
                )
            },
            {
                "chapter_index": 4,
                "timestamp": "07:30",
                "title": "الفصل الثالث: أسرار وحيل لتفادي الأخطاء وهل الوظائف في خطر؟",
                "voiceover": (
                    "في نقطة مهمة جداً معظم الناس بيتجاهلوها، وهي الـ Loop Limits والـ Cost Management. "
                    "لو مكنتش حاطط قيود واضحة للوكيل، ممكن يفضل يلف في دواير مغلقة ويستهلك رصيد الـ API في الفاضي. "
                    "وعشان كده بنحط دايماً شرط أمان (Safety Break). "
                    "أما السؤال اللي بيشغل بال كل الناس: هل ده معناه إن الوظائف هتنتهي؟ "
                    "الحقيقة المؤكدة إن الذكاء الاصطناعي مش هيستبدلك، لكن الشخص اللي بيعرف يشغّل ويدير الـ AI Agents هو اللي هيستبدل أي حد رافض يتعلم."
                )
            },
            {
                "chapter_index": 5,
                "timestamp": "09:30",
                "title": "الخاتمة والدعوة للتفاعل (Conclusion & CTA)",
                "voiceover": (
                    "دي كانت نظرة شاملة وعملية على بداية ثورة الوكلاء الأذكياء. "
                    "كل الروابط، والقوالب الجاهزة (Templates) اللي استخدمناها في الفيديو هتلاقيها في صندوق الوصف بالكامل عشان تبدأ تجرب بإيدك فوراً. "
                    "قولي في التعليقات: إيه أكتر مهمة روتينية بتاخد من وقتك ونفسك تخلي AI Agent يعملها بدالك؟ "
                    "ومتنساش تعمل لايك لو الفيديو قدملك قيمة حقيقية، واشترك في القناة وفعل الجرس عشان يوصلك كل جديد في عالم التكنولوجيا والذكاء الاصطناعي أولاً بأول. سلام!"
                )
            }
        ]
        
        full_vo = "\n\n".join([f"[{c['timestamp']} - {c['title']}]\n{c['voiceover']}" for c in chapters])
        words = len(full_vo.split())
        est_duration = "10 دقائق"
        
        scenes = [
            {
                "scene_number": i + 1,
                "timecode": c["timestamp"],
                "duration_seconds": 120,
                "voiceover": c["voiceover"][:120] + "...",
                "visual_description": f"مشهد مخصص لـ: {c['title']}",
                "b_roll": "لقطات عالية الجودة لشاشات التحكم والبيانات والرسوم البيانية التقنية ثلاثية الأبعاد.",
                "on_screen_text": c["title"],
                "sfx": "Dynamic tech ambiance + subtle transitions",
                "ai_video_prompt": f"Cinematic documentary footage representing {c['title']}, highly detailed tech studio, 4k."
            }
            for i, c in enumerate(chapters)
        ]
        
        return {
            "script_id": f"SCR-LONG-{idea_id}",
            "idea_id": idea_id,
            "video_type": "Long-form",
            "language": "Egyptian Arabic",
            "hook_3s": hook,
            "chapters": chapters,
            "full_voiceover": full_vo,
            "scene_breakdown": scenes,
            "cta": "اشترك في القناة واكتبلي في التعليقات المهمة اللي نفسك تأتمتها!",
            "word_count": words,
            "estimated_duration": est_duration,
            "status": "Ready for Production"
        }

    def save_script_to_database(self, script_data):
        """Saves script record (Firestore when configured, else CSV)."""
        from core import firestore_store
        import datetime
        row = {
            "Script ID": script_data["script_id"],
            "Idea ID": script_data["idea_id"],
            "Video Type": script_data["video_type"],
            "Language": script_data["language"],
            "Hook (0-3s)": script_data["hook_3s"],
            "Full Voiceover (Egyptian Arabic)": script_data["full_voiceover"],
            "Scene Breakdown JSON": json.dumps(script_data["scene_breakdown"], ensure_ascii=False),
            "Suggested CTA": script_data["cta"],
            "Word Count": str(script_data["word_count"]),
            "Estimated Duration": script_data["estimated_duration"],
            "Status": script_data["status"],
            "Script File Link": f"storage/AI Content Factory/2026/{script_data['idea_id']}/Scripts/{script_data['script_id']}.md",
            "Last Updated": datetime.date.today().isoformat(),
        }
        if firestore_store.enabled():
            firestore_store.set_document("scripts", script_data["script_id"], row, merge=True)
            return script_data["script_id"]

        headers = list(row.keys())
        file_exists = self.scripts_csv.exists()
        with open(self.scripts_csv, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow([row[h] for h in headers])
        return script_data["script_id"]
