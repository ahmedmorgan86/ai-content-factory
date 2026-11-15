"""
AI Content Factory - Scenario 5: Thumbnail Generation & Multi-Platform Resizing Engine
Generates cinematic visual prompts, invokes image generation (or renders high-contrast synth visual),
overlays Arabic typography banner, and creates verified YouTube (1280x720) and Vertical (1080x1920) assets.
"""

import os
import json
import csv
import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core.config import Config, DB_DIR

class ThumbnailEngine:
    def __init__(self):
        self.thumbnails_csv = DB_DIR / "Thumbnails.csv"

    def formulate_prompts(self, idea_title, core_concept="AI Agents automation in 2026"):
        """Formulates the exact English prompt for DALL-E 3 and Arabic typography specs."""
        dalle_prompt = (
            f"Hyper-realistic cinematic 8k wide shot representing: '{core_concept}'. "
            f"A glowing futuristic digital assistant hologram with intelligent neural nodes, "
            f"cyberpunk high-contrast ambiance, deep navy slate (#0F172A) background with vivid "
            f"electric cyan (#38BDF8) and ultraviolet indigo rim lighting. "
            f"Dramatic atmospheric mist, octane 3D render style, clean negative space on the left side, "
            f"no text, no letters, no logos, no watermarks, master composition."
        )
        arabic_text = "موظف ذكي 24 ساعة!"
        return dalle_prompt, arabic_text

    def create_cinematic_base_canvas(self, width, height, is_vertical=False):
        """Creates a high-contrast cinematic visual canvas with brand colors & glow effects."""
        base = Image.new("RGB", (width, height), color=(15, 23, 42))  # #0F172A Dark Slate
        draw = ImageDraw.Draw(base)

        # Gradient simulation & atmospheric glow
        for y in range(height):
            ratio = y / height
            # Blend from slate to deep dark blue
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
        """Adds Arabic text banner and channel branding overlay."""
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
            box_x0, box_y0 = int(w * 0.05), int(h * 0.28)
            box_x1, box_y1 = int(w * 0.48), int(h * 0.65)
            # Dark backing for maximum mobile contrast
            draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=(15, 23, 42))
            draw.rectangle([box_x0, box_y0, box_x1, box_y1], outline=(56, 189, 248), width=4)
            # Brand tag
            draw.rectangle([box_x0 + 15, box_y0 - 20, box_x0 + 220, box_y0 + 15], fill=(56, 189, 248))
            draw.text((box_x0 + 25, box_y0 - 18), "AI CONTENT FACTORY", fill=(15, 23, 42), font=tag_font)
            # Arabic headline text
            draw.text((box_x0 + 25, box_y0 + 40), arabic_headline, fill=(255, 255, 255), font=headline_font)
            draw.text((box_x0 + 25, box_y0 + 120), "دليل 2026 الحصري 🔥", fill=(56, 189, 248), font=headline_font)
        else:
            # Vertical 9:16 (1080x1920)
            box_x0, box_y0 = int(w * 0.08), int(h * 0.68)
            box_x1, box_y1 = int(w * 0.92), int(h * 0.88)
            draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=(15, 23, 42))
            draw.rectangle([box_x0, box_y0, box_x1, box_y1], outline=(56, 189, 248), width=5)
            # Brand tag
            draw.rectangle([box_x0 + 25, box_y0 - 25, box_x0 + 340, box_y0 + 22], fill=(56, 189, 248))
            draw.text((box_x0 + 35, box_y0 - 22), "SHORTS & REELS EXCLUSIVE", fill=(15, 23, 42), font=tag_font)
            # Headline
            draw.text((box_x0 + 35, box_y0 + 50), arabic_headline, fill=(255, 255, 255), font=headline_font)
            draw.text((box_x0 + 35, box_y0 + 160), "أتمتة ذكية بدون كود ⚡", fill=(56, 189, 248), font=headline_font)

        return img

    def generate_and_verify_thumbnails(self, idea_id, title, output_dir=None):
        """
        Executes full thumbnail pipeline:
        1. Builds prompts.
        2. Generates base.
        3. Creates and verifies 1280x720 (YouTube 16:9).
        4. Creates and verifies 1080x1920 (Shorts/TikTok/Reels 9:16).
        5. Saves to disk and verifies exact dimensions.
        """
        if output_dir is None:
            output_dir = Path(__file__).resolve().parent.parent / "storage" / "AI Content Factory" / "2026" / idea_id / "Thumbnails"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        dalle_prompt, arabic_headline = self.formulate_prompts(title)

        # 1. YouTube Long (1280 x 720)
        yt_base = self.create_cinematic_base_canvas(1280, 720, is_vertical=False)
        yt_final = self.add_arabic_and_branding_overlays(yt_base, arabic_headline, is_vertical=False)
        yt_path = output_dir / f"thumbnail_{idea_id}_youtube_1280x720.jpg"
        yt_final.save(yt_path, format="JPEG", quality=95)

        # 2. Vertical Shorts / Reels / TikTok (1080 x 1920)
        v_base = self.create_cinematic_base_canvas(1080, 1920, is_vertical=True)
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
            "raw_url": "Generated & Verified Local Render",
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
