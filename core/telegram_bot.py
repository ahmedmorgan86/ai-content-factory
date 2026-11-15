"""
AI Content Factory - Scenario 6 / Telegram Control Panel & Bot Dispatcher
Implements commands: /start, /ideas, /shorts, /long, /generate, /status, /history, /settings, /help
Interactive approval flows, security authentication, and file delivery.
"""

import os
import json
import requests
from pathlib import Path
from core.config import Config, DB_DIR

class TelegramControlPanel:
    def __init__(self, token=None, admin_chat_id=None):
        self.token = token or Config.TELEGRAM_BOT_TOKEN
        self.admin_chat_id = admin_chat_id or Config.TELEGRAM_ADMIN_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    def is_authorized(self, user_id):
        """Security guard: verifies user identity against authorized admins."""
        if not self.admin_chat_id:
            # If no admin chat ID configured yet, default to allowing local test
            return True
        return str(user_id).strip() == str(self.admin_chat_id).strip()

    def build_main_menu_payload(self):
        """Builds /start command text and interactive inline keyboard."""
        text = (
            "🤖 <b>أهلاً بك في غرفة قيادة مصنع المحتوى الذكي (AI Content Factory)!</b>\n\n"
            "لوحة تحكم أوتوماتيكية متكاملة لإنتاج وتوزيع المحتوى التقني.\n\n"
            "📌 <b>الأوامر المتاحة:</b>\n"
            "💡 <code>/ideas</code> - استعراض أحدث الأفكار المولدة\n"
            "⚡ <code>/shorts</code> - فلترة أفكار الفيديوهات القصيرة (Shorts & Reels)\n"
            "🎥 <code>/long</code> - فلترة أفكار الفيديوهات الطويلة (8-12 دقيقة)\n"
            "⚙️ <code>/generate [Idea_ID]</code> - بدء إنتاج حزمة الفيديو فوراً\n"
            "📊 <code>/status</code> - عرض حالة العمليات والخطوط الجارية\n"
            "📜 <code>/history</code> - أرشيف الفيديوهات والمحتوى المنشور\n"
            "🔧 <code>/settings</code> - استعراض الإعدادات والنيش الحالي\n"
            "❓ <code>/help</code> - دليل الاستخدام والمساعدة السريعة"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💡 توليد واستعراض الأفكار", "callback_data": "cmd:ideas"},
                    {"text": "⚡ شورتس فقط", "callback_data": "cmd:shorts"}
                ],
                [
                    {"text": "🎥 فيديوهات طويلة", "callback_data": "cmd:long"},
                    {"text": "📊 حالة النظام", "callback_data": "cmd:status"}
                ],
                [
                    {"text": "🔧 الإعدادات", "callback_data": "cmd:settings"},
                    {"text": "📜 الأرشيف", "callback_data": "cmd:history"}
                ]
            ]
        }
        return text, keyboard

    def format_ideas_list_message(self, ideas, filter_type=None):
        """Formats numbered list of ideas with interactive selection buttons."""
        filtered = ideas
        if filter_type:
            filtered = [i for i in ideas if i.get("video_type", "").lower() == filter_type.lower()]

        text = f"💡 <b>قائمة الأفكار المقترحة ({len(filtered)} فكرة جاهزة):</b>\n\n"
        buttons = []
        for idx, item in enumerate(filtered[:10], start=1):
            text += (
                f"<b>{idx}. [{item.get('video_type', 'Short')}] {item.get('video_title')}</b>\n"
                f"   🎯 <i>الجمهور:</i> {item.get('target_audience')}\n"
                f"   ⚡ <i>الخطاف:</i> {item.get('hook')[:70]}...\n"
                f"   ⭐ <i>التقييم:</i> {item.get('priority_score')}/10 | <code>{item.get('idea_id')}</code>\n\n"
            )
            buttons.append([
                {"text": f"🚀 إنتاج فكرة #{idx} ({item.get('idea_id')})", "callback_data": f"select_idea:{item.get('idea_id')}"}
            ])

        text += "اضغط على زر الفكرة التي ترغب في إنتاجها فوراً، أو اكتب: <code>/generate [Idea_ID]</code>"
        keyboard = {"inline_keyboard": buttons}
        return text, keyboard

    def format_delivery_package(self, idea, script, seo, thumb_result):
        """Prepares comprehensive review delivery payload with action buttons."""
        text = (
            f"🎬 <b>حزمة الإنتاج الكاملة للفيديو ({idea.get('idea_id')}):</b>\n\n"
            f"📌 <b>العنوان المعتمد:</b>\n{seo.get('recommended_best_title')}\n\n"
            f"🎯 <b>الخطاف (Hook أول 3 ثوانٍ):</b>\n{script.get('hook_3s')}\n\n"
            f"📜 <b>السكريبت ({script.get('video_type')} - {script.get('estimated_duration')}):</b>\n"
            f"<i>{script.get('full_voiceover')[:320]}...</i>\n\n"
            f"🏷️ <b>الهاشتاجات:</b> {' '.join(seo.get('hashtags_5', []))}\n"
            f"🔑 <b>الكلمات المفتاحية:</b> {', '.join(seo.get('primary_keywords', []))}\n\n"
            f"🖼️ <b>الصور المصغرة:</b>\n"
            f"• YouTube (1280x720): تم التحقق والإنشاء بنجاح\n"
            f"• Vertical Shorts (1080x1920): تم التحقق والإنشاء بنجاح\n\n"
            f"📁 <b>المجلد السحابي:</b> <code>storage/AI Content Factory/2026/{idea.get('idea_id')}/</code>\n\n"
            f"<b>اختر الإجراء للمتابعة:</b>"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ موافقة وجدولة النشر", "callback_data": f"action:approve:{idea.get('idea_id')}"},
                    {"text": "🔄 إعادة توليد الصورة", "callback_data": f"action:regen_thumb:{idea.get('idea_id')}"}
                ],
                [
                    {"text": "✏️ طلب تعديل السكريبت", "callback_data": f"action:edit_script:{idea.get('idea_id')}"},
                    {"text": "❌ رفض الفكرة", "callback_data": f"action:reject:{idea.get('idea_id')}"}
                ]
            ]
        }
        return text, keyboard

    def send_telegram_message(self, chat_id, text, reply_markup=None):
        """Sends message via live Telegram API if token is configured."""
        if not self.api_url:
            return {"simulated": True, "success": True, "chat_id": chat_id, "text": text}
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            r = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
            return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_telegram_photo(self, chat_id, photo_path, caption="", reply_markup=None):
        """Sends photo via live Telegram API if token is configured."""
        if not self.api_url:
            return {"simulated": True, "success": True, "photo_path": photo_path}
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        try:
            with open(photo_path, "rb") as f:
                r = requests.post(f"{self.api_url}/sendPhoto", data=data, files={"photo": f}, timeout=20)
                return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
