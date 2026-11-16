"""
AI Content Factory - Scenario 5: Real AI Thumbnail & Multi-Platform Resizing Engine
Generates photorealistic AI artwork via Flux / DALL-E, overlays Arabic typography,
and creates verified YouTube (1280x720) and Vertical (1080x1920) assets.
"""

import os
import io
import json
import csv
import random
import datetime
import urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from core.config import Config, DB_DIR

class ThumbnailEngine:
    def __init__(self):
        self.thumbnails_csv = DB_DIR / "Thumbnails.csv"

    def formulate_prompts(self, idea_title, core_concept="AI Agents automation in 2026"):
        """Formulates the exact English prompt for AI Art generation and Arabic typography specs."""
        clean_concept = idea_title if idea_title else core_concept
        dalle_prompt = (
            f"Hyper-realistic cinematic 8k wide shot representing: '{clean_concept}'. "
            f"A glowing futuristic digital assistant hologram with intelligent neural nodes, "
            f"cyberpunk high-contrast ambiance, deep navy slate (#0F172A) background with vivid "
            f"electric cyan (#38BDF8) and ultraviolet indigo rim lighting. "
            f"Dramatic atmospheric mist, octane 3D render style, clean negative space on the left side, "
            f"no text, no letters, no logos, no watermarks, master composition."
        )
        arabic_text = "موظف ذكي 24 ساعة!"
        if "فلوس" in clean_concept or "ربح" in clean_concept or "دخل" in clean_concept:
            arabic_text = "دخل يومي بالذكاء الاصطناعي 💰"
        elif "أداة" in clean_concept or "برنامج" in clean_concept:
            arabic_text = "أقوى أدوات 2026 الخارقة ⚡"
        elif "سر" in clean_concept or "خدعة" in clean_concept:
            arabic_text = "السر اللي مخبينه عليك! 🤫"
            
        return dalle_prompt, arabic_text

    def fetch_real_ai_artwork(self, prompt, width, height, seed=None):
        """
        Fetches photorealistic 8K AI artwork using Pollinations Flux engine.
        Falls back seamlessly to synthetic dark slate canvas if offline or timeout.
        """
        if seed is None:
            seed = random.randint(1000, 999999)

        if Config.GOOGLE_USE_IMAGEN:
            if not Config.GEMINI_API_KEY:
                raise RuntimeError("Google Imagen is enabled but GEMINI_API_KEY is not configured.")
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=Config.GEMINI_API_KEY)
                model = Config.GOOGLE_IMAGE_MODEL or "imagen-4.0-generate-001"
                result = client.models.generate_images(model=model, prompt=prompt, config=types.GenerateImagesConfig(number_of_images=1))
                image_bytes = result.generated_images[0].image.image_bytes
                img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                if img.size != (width, height):
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                return img, f"Google Imagen ({model})"
            except Exception as exc:
                raise RuntimeError(f"Google Imagen generation failed: {exc}") from exc
            
        try:
            encoded = urllib.parse.quote(prompt[:300])
            url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&model=flux&nologo=true&seed={seed}"
            headers = {"User-Agent": "AIContentFactory/2.0"}
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200 and len(resp.content) > 5000:
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                if img.size != (width, height):
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                return img, "AI Flux Generation"
        except Exception as e:
            # Fallback gracefully
            pass

        return self.create_cinematic_base_canvas(width, height, is_vertical=(height > width)), "Synthetic Fallback"

    def create_cinematic_base_canvas(self, width, height, is_vertical=False):
        """Creates a high-contrast cinematic visual canvas with brand colors & glow effects as fallback."""
        base = Image.new("RGB", (width, height), color=(15, 23, 42))  # #0F172A Dark Slate
        draw = ImageDraw.Draw(base)

        # Gradient simulation & atmospheric glow
        for y in range(height):
            ratio = y / height
            r = int(15 * (1 - ratio) + 8 * ratio)
            g = int(23 * (1 - ratio) + 14 * ratio)
            b = int(42 * (1 - ratio) + 30 * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Add tech grid overlay
        grid_step = 60
        for x in range(0, width, grid_step):
            draw.line([(x, 0), (x, height)], fill=(24, 38, 68), width=1)
        for y in range(0, height, grid_step):
            draw.line([(0, y), (width, y)], fill=(24, 38, 68), width=1)

        # Core glowing circular AI focal element
        center_x = int(width * 0.65) if not is_vertical else int(width * 0.5)
        center_y = int(height * 0.5) if not is_vertical else int(height * 0.42)
        radius = int(min(width, height) * 0.28)

        # Ambient glow behind core
        for r_offset in range(radius + 80, radius, -5):
            alpha_ratio = (radius + 80 - r_offset) / 80
            glow_col = (int(56 * alpha_ratio), int(189 * alpha_ratio), int(248 * alpha_ratio)) # Cyan glow
            draw.ellipse(
                [center_x - r_offset, center_y - r_offset, center_x + r_offset, center_y + r_offset],
                outline=glow_col, width=2
            )

        # Central core sphere & rings
        draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            fill=(14, 116, 144), outline=(56, 189, 248), width=6
        )

        # Inner neural core
        inner_r = int(radius * 0.55)
        draw.ellipse(
            [center_x - inner_r, center_y - inner_r, center_x + inner_r, center_y + inner_r],
            fill=(129, 140, 248), outline=(255, 255, 255), width=3
        )

        return base

    def add_arabic_and_branding_overlays(self, image, arabic_headline, is_vertical=False):
        """Adds high-contrast Arabic text banner, gradient scrim, and channel branding overlay."""
        img = image.copy()
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Find system font or fallback
        font_paths = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/tahomabd.ttf"
        ]
        headline_font = None
        tag_font = None
        for p in font_paths:
            if os.path.exists(p):
                try:
                    font_size = int(h * 0.085) if not is_vertical else int(w * 0.08)
                    headline_font = ImageFont.truetype(p, font_size)
                    tag_font = ImageFont.truetype(p, int(font_size * 0.45))
                    break
                except Exception:
                    continue

        if headline_font is None:
            headline_font = ImageFont.load_default()
            tag_font = ImageFont.load_default()

        # Banner Box
        if not is_vertical:
            # YouTube 16:9 (1280x720)
            box_x0, box_y0 = int(w * 0.04), int(h * 0.25)
            box_x1, box_y1 = int(w * 0.52), int(h * 0.70)
            
            # Semi-dark backing with vivid cyan border for extreme mobile readability
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rounded_rectangle([box_x0, box_y0, box_x1, box_y1], radius=16, fill=(15, 23, 42, 230), outline=(56, 189, 248, 255), width=4)
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

            # Brand tag
            draw.rounded_rectangle([box_x0 + 15, box_y0 - 18, box_x0 + 230, box_y0 + 18], radius=6, fill=(56, 189, 248))
            draw.text((box_x0 + 25, box_y0 - 15), "AI CONTENT FACTORY", fill=(15, 23, 42), font=tag_font)

            # Arabic headline text
            draw.text((box_x0 + 25, box_y0 + 40), arabic_headline, fill=(255, 255, 255), font=headline_font)
            draw.text((box_x0 + 25, box_y0 + 125), "دليل 2026 الحصري 🔥", fill=(56, 189, 248), font=headline_font)
        else:
            # Vertical 9:16 (1080x1920)
            box_x0, box_y0 = int(w * 0.06), int(h * 0.65)
            box_x1, box_y1 = int(w * 0.94), int(h * 0.88)
            
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rounded_rectangle([box_x0, box_y0, box_x1, box_y1], radius=20, fill=(15, 23, 42, 235), outline=(56, 189, 248, 255), width=5)
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

            # Brand tag
            draw.rounded_rectangle([box_x0 + 25, box_y0 - 24, box_x0 + 360, box_y0 + 24], radius=8, fill=(56, 189, 248))
            draw.text((box_x0 + 35, box_y0 - 20), "SHORTS & REELS EXCLUSIVE", fill=(15, 23, 42), font=tag_font)

            # Headline
            draw.text((box_x0 + 35, box_y0 + 50), arabic_headline, fill=(255, 255, 255), font=headline_font)
            draw.text((box_x0 + 35, box_y0 + 160), "أتمتة ذكية بدون كود ⚡", fill=(56, 189, 248), font=headline_font)

        return img

    def generate_and_verify_thumbnails(self, idea_id, title, output_dir=None):
        """
        Executes full thumbnail pipeline:
        1. Builds prompts.
        2. Generates real AI artwork via Flux / DALL-E (or fallback).
        3. Creates and verifies 1280x720 (YouTube 16:9).
        4. Creates and verifies 1080x1920 (Shorts/TikTok/Reels 9:16).
        5. Saves to disk and verifies exact dimensions.
        """
        if output_dir is None:
            output_dir = Path(__file__).resolve().parent.parent / "storage" / "AI Content Factory" / "2026" / idea_id / "Thumbnails"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        dalle_prompt, arabic_headline = self.formulate_prompts(title)

        # 1. YouTube Long (1280 x 720) Real AI Base
        yt_base, gen_source = self.fetch_real_ai_artwork(dalle_prompt, 1280, 720)
        yt_final = self.add_arabic_and_branding_overlays(yt_base, arabic_headline, is_vertical=False)
        yt_path = output_dir / f"thumbnail_{idea_id}_youtube_1280x720.jpg"
        yt_final.save(yt_path, format="JPEG", quality=95)

        # 2. Vertical Shorts / Reels / TikTok (1080 x 1920) Real AI Base
        v_base, _ = self.fetch_real_ai_artwork(dalle_prompt, 1080, 1920)
        v_final = self.add_arabic_and_branding_overlays(v_base, arabic_headline, is_vertical=True)
        v_path = output_dir / f"cover_{idea_id}_vertical_1080x1920.jpg"
        v_final.save(v_path, format="JPEG", quality=95)

        # VERIFICATION OF DIMENSIONS
        with Image.open(yt_path) as check_yt:
            assert check_yt.size == (1280, 720), f"YouTube thumbnail size mismatch: {check_yt.size}"
        with Image.open(v_path) as check_v:
            assert check_v.size == (1080, 1920), f"Vertical cover size mismatch: {check_v.size}"

        # Record to database
        thumbnail_id = f"THUMB-{idea_id}"
        self.save_thumbnail_to_database({
            "thumbnail_id": thumbnail_id,
            "idea_id": idea_id,
            "prompt": dalle_prompt,
            "raw_url": f"Pollinations Flux AI ({gen_source})",
            "yt_link": str(yt_path),
            "v_link": str(v_path),
            "personal_photo": "No",
            "arabic_text": arabic_headline,
            "storage_path": str(output_dir),
            "dimensions_verified": "Verified (1280x720 & 1080x1920)",
            "status": "Generated & Verified",
            "created_date": datetime.date.today().isoformat()
        })

        return {
            "thumbnail_id": thumbnail_id,
            "youtube_path": str(yt_path),
            "vertical_path": str(v_path),
            "youtube_dimensions": (1280, 720),
            "vertical_dimensions": (1080, 1920),
            "generation_source": gen_source,
            "status": "Success & Verified"
        }

    def save_thumbnail_to_database(self, record):
        headers = [
            "Thumbnail ID", "Idea ID", "Visual Concept & AI Prompt", "Raw Image URL", 
            "YouTube 16:9 (1280x720) Link", "Vertical 9:16 (1080x1920) Link", 
            "Personal Photo Included", "Arabic Text Overlay", "Storage Path / Cloudinary ID", 
            "Dimensions Verified", "Status", "Created Date"
        ]
        file_exists = self.thumbnails_csv.exists()
        with open(self.thumbnails_csv, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow([
                record["thumbnail_id"],
                record["idea_id"],
                record["prompt"],
                record["raw_url"],
                record["yt_link"],
                record["v_link"],
                record["personal_photo"],
                record["arabic_text"],
                record["storage_path"],
                record["dimensions_verified"],
                record["status"],
                record["created_date"]
            ])
