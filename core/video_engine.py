"""
AI Content Factory - Scenario 8: Automated Video Assembly & Rendering Engine
Takes scenes, visual prompts, and VoxArabic voiceover audio to assemble complete,
ready-for-publishing MP4 videos (Shorts/Reels 9:16 or YouTube Long 16:9).
"""

import os
import io
import json
import csv
import random
import datetime
import urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests

from core.config import Config, DB_DIR, STORAGE_ROOT
from core.voice_engine import VoiceEngine
from core.thumbnail_engine import ThumbnailEngine

class VideoEngine:
    def __init__(self):
        self.videos_csv = DB_DIR / "Videos.csv"
        self.voice_engine = VoiceEngine()
        self.thumbnail_engine = ThumbnailEngine()

    def generate_scene_image(self, prompt, text_overlay, width, height, scene_index=1, total_scenes=4):
        """
        Generates a high-quality visual for a scene using real AI art and overlays modern Arabic subtitles/text card.
        """
        # Fetch real AI visual or fallback
        base_img, source = self.thumbnail_engine.fetch_real_ai_artwork(prompt, width, height)
        img = base_img.copy()

        # Overlay scene text card
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Font setup
        font_paths = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/tahomabd.ttf"
        ]
        text_font = None
        badge_font = None
        for p in font_paths:
            if os.path.exists(p):
                try:
                    font_size = int(h * 0.045) if height > width else int(h * 0.065)
                    text_font = ImageFont.truetype(p, font_size)
                    badge_font = ImageFont.truetype(p, int(font_size * 0.55))
                    break
                except Exception:
                    continue

        if text_font is None:
            text_font = ImageFont.load_default()
            badge_font = ImageFont.load_default()

        # Lower-third or center card
        if height > width:
            # Vertical (1080x1920) Shorts / Reels
            card_x0, card_y0 = int(w * 0.08), int(h * 0.65)
            card_x1, card_y1 = int(w * 0.92), int(h * 0.82)
            
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=24, fill=(15, 23, 42, 220), outline=(56, 189, 248, 255), width=4)
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

            # Scene badge
            draw.rounded_rectangle([card_x0 + 20, card_y0 - 20, card_x0 + 220, card_y0 + 18], radius=8, fill=(56, 189, 248))
            draw.text((card_x0 + 30, card_y0 - 16), f"مشهد {scene_index} من {total_scenes}", fill=(15, 23, 42), font=badge_font)

            # Text
            draw.text((card_x0 + 30, card_y0 + 40), text_overlay, fill=(255, 255, 255), font=text_font)
        else:
            # Horizontal (1280x720) YouTube Long
            card_x0, card_y0 = int(w * 0.05), int(h * 0.68)
            card_x1, card_y1 = int(w * 0.70), int(h * 0.90)
            
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=16, fill=(15, 23, 42, 220), outline=(56, 189, 248, 255), width=3)
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

            # Scene badge
            draw.rounded_rectangle([card_x0 + 15, card_y0 - 16, card_x0 + 180, card_y0 + 15], radius=6, fill=(56, 189, 248))
            draw.text((card_x0 + 25, card_y0 - 13), f"مشهد {scene_index} من {total_scenes}", fill=(15, 23, 42), font=badge_font)

            # Text
            draw.text((card_x0 + 25, card_y0 + 35), text_overlay, fill=(255, 255, 255), font=text_font)

        return img

    def render_video_for_idea(self, idea_id, script_data=None, voice_key="shakir", is_vertical=True, fps=24, video_type=None):
        """
        End-to-End Video Production Pipeline:
        1. Ensures Egyptian Arabic audio voiceover exists (or generates it).
        2. Retrieves scene breakdown.
        3. Generates AI visual frames for each scene with on-screen text badges.
        4. Stitches visual clips and aligns durations with total audio runtime.
        5. Attaches voiceover audio track and encodes into broadcast MP4.
        6. Saves video file and registers in database.
        """
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

        video_assets_dir = STORAGE_ROOT / idea_id / "Video_Assets"
        audio_dir = STORAGE_ROOT / idea_id / "Audio"
        video_assets_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # 1. Obtain script & voiceover text
        if script_data is None:
            # Try to load existing script from storage
            scripts_dir = STORAGE_ROOT / idea_id / "Scripts"
            scene_files = list(scripts_dir.glob("scenes_*.json")) if scripts_dir.exists() else []
            if scene_files:
                with open(scene_files[0], "r", encoding="utf-8") as f:
                    scenes = json.load(f)
                voiceover_text = " ".join([s.get("voiceover", "") for s in scenes])
                script_data = {"scene_breakdown": scenes, "full_voiceover": voiceover_text}
            else:
                # Generate default script
                from core.script_engine import ScriptEngine
                se = ScriptEngine()
                script_data = se.generate_short_script({"idea_id": idea_id, "video_title": f"فيديو {idea_id}"})

        scenes = script_data.get("scene_breakdown", [])
        if not scenes:
            raise ValueError(f"No scene breakdown found for {idea_id}")

        full_voiceover = script_data.get("full_voiceover", "")

        # 2. Ensure voiceover audio exists
        voice_type = video_type or ("Short-form" if is_vertical else "Long-form")
        extension = "wav" if voice_key.startswith("google_") else "mp3"
        audio_path = audio_dir / f"voiceover_{idea_id}_{voice_key}.{extension}"
        if not audio_path.exists():
            voice_res = self.voice_engine.generate_voiceover(
                idea_id=idea_id,
                text=full_voiceover,
                voice_key=voice_key,
                output_dir=audio_dir,
                video_type=voice_type
            )
            audio_path = Path(voice_res["file_path"])

        # Measure audio duration
        audio_clip = AudioFileClip(str(audio_path))
        total_audio_duration = audio_clip.duration
        if total_audio_duration <= 0:
            total_audio_duration = 30.0

        # 3. Calculate per-scene durations
        total_scenes = len(scenes)
        # Allocate duration based on voiceover length in each scene or evenly
        scene_word_counts = [max(1, len(s.get("voiceover", "").split())) for s in scenes]
        total_words = sum(scene_word_counts)
        scene_durations = [(wc / total_words) * total_audio_duration for wc in scene_word_counts]

        # 4. Generate scene frames and moviepy ImageClips
        width, height = (1080, 1920) if is_vertical else (1280, 720)
        clips = []
        frame_paths = []

        for idx, scene in enumerate(scenes):
            scene_num = idx + 1
            prompt = scene.get("ai_video_prompt") or scene.get("visual_description") or f"Cinematic scene for {idea_id}"
            text_overlay = scene.get("on_screen_text") or scene.get("voiceover", "")[:40]
            dur = max(1.5, scene_durations[idx])

            # Generate frame
            frame_img = self.generate_scene_image(
                prompt=prompt,
                text_overlay=text_overlay,
                width=width,
                height=height,
                scene_index=scene_num,
                total_scenes=total_scenes
            )
            frame_file = video_assets_dir / f"frame_scene_{scene_num}_{width}x{height}.jpg"
            frame_img.save(frame_file, format="JPEG", quality=92)
            frame_paths.append(str(frame_file))

            # Create clip
            clip = ImageClip(str(frame_file)).with_duration(dur)
            clips.append(clip)

        # 5. Concatenate & attach audio
        video = concatenate_videoclips(clips, method="compose")
        # Ensure exact match with audio duration
        video = video.with_duration(total_audio_duration)
        video = video.with_audio(audio_clip)

        # 6. Render MP4
        output_filename = f"final_video_{idea_id}_{'vertical' if is_vertical else 'horizontal'}.mp4"
        output_path = video_assets_dir / output_filename

        video.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )

        # Clean up moviepy handles
        audio_clip.close()
        video.close()

        filesize = output_path.stat().st_size if output_path.exists() else 0
        video_id = f"VID-{idea_id}-{'V' if is_vertical else 'H'}"

        # 7. Record to database
        self.save_video_to_database({
            "video_id": video_id,
            "idea_id": idea_id,
            "aspect_ratio": "9:16 Vertical" if is_vertical else "16:9 Horizontal",
            "resolution": f"{width}x{height}",
            "duration_seconds": round(total_audio_duration, 2),
            "file_size_bytes": filesize,
            "file_path": str(output_path),
            "voice_used": voice_key,
            "total_scenes": total_scenes,
            "status": "Ready for Publishing",
            "created_date": datetime.date.today().isoformat()
        })

        return {
            "video_id": video_id,
            "idea_id": idea_id,
            "file_path": str(output_path),
            "filename": output_filename,
            "duration_seconds": round(total_audio_duration, 2),
            "resolution": f"{width}x{height}",
            "file_size": filesize,
            "aspect_ratio": "9:16 Vertical" if is_vertical else "16:9 Horizontal",
            "scenes_count": total_scenes,
            "status": "Ready for Publishing"
        }

    def save_video_to_database(self, record):
        headers = [
            "Video ID", "Idea ID", "Aspect Ratio", "Resolution", "Duration (s)",
            "File Size (Bytes)", "File Path", "Voice Used", "Total Scenes",
            "Status", "Created Date"
        ]
        file_exists = self.videos_csv.exists()
        with open(self.videos_csv, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow([
                record["video_id"],
                record["idea_id"],
                record["aspect_ratio"],
                record["resolution"],
                record["duration_seconds"],
                record["file_size_bytes"],
                record["file_path"],
                record["voice_used"],
                record["total_scenes"],
                record["status"],
                record["created_date"]
            ])
