"""
AI Content Factory - Scenario 7: VoxArabicStudio Voice Engine
Integrates voiceover synthesis based on ahmedmorgan86/VoxArabicStudio
Produces authentic Egyptian Arabic voiceovers (اللهجة المصرية) using Edge-TTS Studio Neural voices
and Google Gemini Audio API.
"""

import os
import csv
import json
import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from core.config import Config, DB_DIR, STORAGE_ROOT

VOICE_PROFILES = {
    "shakir": {
        "id": "ar-EG-ShakirNeural",
        "name": "شاكر (استوديو احترافي - ذكر)",
        "gender": "Male",
        "dialect": "Egyptian Arabic",
        "description": "صوت إذاعي مصري دافئ وحيوي، مثالي للشروحات والفيديوهات التقنية"
    },
    "salma": {
        "id": "ar-EG-SalmaNeural",
        "name": "سلمى (استوديو إذاعي - أنثى)",
        "gender": "Female",
        "dialect": "Egyptian Arabic",
        "description": "صوت مصري طبيعي ونشيط، ممتاز للريلز والشورتس السريعة"
    }
}

class VoiceEngine:
    def __init__(self):
        self.audio_csv = DB_DIR / "Audio.csv"

    def get_available_voices(self):
        """Returns the available Egyptian voice profiles."""
        return VOICE_PROFILES

    async def _synthesize_edge_tts(self, text, voice_id, output_path, rate="+0%", pitch="+0Hz"):
        """Asynchronously synthesizes speech using edge-tts."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
        await communicate.save(str(output_path))

    def generate_voiceover(self, idea_id, text, voice_key="shakir", output_dir=None, rate="+0%"):
        """
        Synthesizes authentic Egyptian voiceover for a given script text.
        Saves the audio file as MP3 and records metadata in database/Audio.csv.
        """
        if not text or not text.strip():
            raise ValueError("Voiceover text cannot be empty.")

        if output_dir is None:
            output_dir = STORAGE_ROOT / idea_id / "Audio"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        voice_info = VOICE_PROFILES.get(voice_key, VOICE_PROFILES["shakir"])
        voice_id = voice_info["id"]

        filename = f"voiceover_{idea_id}_{voice_key}.mp3"
        output_path = output_dir / filename

        # Run edge-tts synthesis safely across sync and async contexts
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(
                    lambda: asyncio.run(self._synthesize_edge_tts(text, voice_id, output_path, rate=rate))
                ).result()
        except Exception as e:
            raise RuntimeError(f"Audio synthesis failed: {e}")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Voiceover generation failed: File was not created at {output_path}")

        # Compute duration estimate or use audio file length
        audio_size = output_path.stat().st_size
        word_count = len(text.split())
        est_duration = round(word_count / 2.3, 1)

        # Try to get exact duration via moviepy / mutagen if possible
        actual_duration = est_duration
        try:
            from moviepy import AudioFileClip
            with AudioFileClip(str(output_path)) as aclip:
                actual_duration = round(aclip.duration, 2)
        except Exception:
            pass

        audio_id = f"AUD-{idea_id}-{voice_key}"
        self.save_audio_to_database({
            "audio_id": audio_id,
            "idea_id": idea_id,
            "voice_name": voice_info["name"],
            "voice_id": voice_id,
            "file_path": str(output_path),
            "file_size_bytes": audio_size,
            "duration_seconds": actual_duration,
            "word_count": word_count,
            "text_sample": text[:80] + "...",
            "status": "Ready",
            "created_date": datetime.date.today().isoformat()
        })

        return {
            "audio_id": audio_id,
            "idea_id": idea_id,
            "voice": voice_info,
            "file_path": str(output_path),
            "filename": filename,
            "file_size": audio_size,
            "duration_seconds": actual_duration,
            "status": "Ready"
        }

    def save_audio_to_database(self, record):
        headers = [
            "Audio ID", "Idea ID", "Voice Name", "Voice ID", "File Path",
            "File Size (Bytes)", "Duration (s)", "Word Count", "Text Sample",
            "Status", "Created Date"
        ]
        file_exists = self.audio_csv.exists()
        with open(self.audio_csv, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow([
                record["audio_id"],
                record["idea_id"],
                record["voice_name"],
                record["voice_id"],
                record["file_path"],
                record["file_size_bytes"],
                record["duration_seconds"],
                record["word_count"],
                record["text_sample"],
                record["status"],
                record["created_date"]
            ])
