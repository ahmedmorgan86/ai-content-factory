"""
AI Content Factory - Scenario 7: VoxArabicStudio Voice Engine
Integrates voiceover synthesis based on ahmedmorgan86/VoxArabicStudio
Produces authentic Egyptian Arabic voiceovers (اللهجة المصرية) using Edge-TTS Studio Neural voices
and Google Gemini Audio API.
"""

import csv
import json
import asyncio
import datetime
import io
import re
import struct
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
    },
    "google_kore": {"id": "Kore", "name": "Kore (Google Gemini - أنثى)", "gender": "Female", "dialect": "Multilingual / Egyptian Arabic", "description": "صوت Google Gemini قابل لتوجيه اللهجة المصرية والأسلوب"},
    "google_puck": {"id": "Puck", "name": "Puck (Google Gemini - ذكر)", "gender": "Male", "dialect": "Multilingual / Egyptian Arabic", "description": "صوت Google Gemini حيوي للفيديوهات القصيرة"},
    "google_charon": {"id": "Charon", "name": "Charon (Google Gemini - عميق)", "gender": "Male", "dialect": "Multilingual / Egyptian Arabic", "description": "صوت Google Gemini عميق للفيديوهات الطويلة والوثائقية"},
    "google_fenrir": {"id": "Fenrir", "name": "Fenrir (Google Gemini - قوي)", "gender": "Male", "dialect": "Multilingual / Egyptian Arabic", "description": "صوت Google Gemini قوي للإلقاء الحماسي"},
    "google_zephyr": {"id": "Zephyr", "name": "Zephyr (Google Gemini - هادئ)", "gender": "Female", "dialect": "Multilingual / Egyptian Arabic", "description": "صوت Google Gemini هادئ وطبيعي"},
}

GOOGLE_VOICES = {"google_kore", "google_puck", "google_charon", "google_fenrir", "google_zephyr"}
VOICE_STYLES = {
    "Short-form": "Energetic, friendly Egyptian Arabic creator delivery, lively pacing, clear punchy emphasis, natural Cairo dialect.",
    "Long-form": "Warm, confident Egyptian Arabic documentary educator narration, measured pacing, clear articulation, natural Cairo dialect.",
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

    @staticmethod
    def _pcm_to_wav(pcm, sample_rate=24000, channels=1, sample_width=2):
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " +
                struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, sample_width * 8) +
                b"data" + struct.pack("<I", len(pcm)) + pcm)

    @staticmethod
    def _clean_tts_text(text):
        text = re.sub(r"<[^>]+>|\|(yeah|mhm)\|", "", text, flags=re.IGNORECASE)
        text = re.sub(r"[*_#`]+", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def _synthesize_gemini(self, text, voice_key, video_type, output_path):
        if not Config.GEMINI_API_KEY:
            raise RuntimeError("Google Gemini is selected but GEMINI_API_KEY is not configured.")
        from google import genai
        from google.genai import types

        voice_info = VOICE_PROFILES[voice_key]
        style = VOICE_STYLES.get(video_type, VOICE_STYLES["Short-form"])
        cleaned_text = self._clean_tts_text(text)
        paragraphs = [p.strip() for p in re.split(r"(?<=[.!?؟])\s+|\n+", cleaned_text) if p.strip()]
        chunks, current = [], ""
        for paragraph in paragraphs:
            if len(paragraph) > 2400:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(paragraph[i:i + 2400] for i in range(0, len(paragraph), 2400))
            elif current and len(current) + len(paragraph) + 1 > 2400:
                chunks.append(current)
                current = paragraph
            else:
                current = f"{current} {paragraph}".strip()
        if current:
            chunks.append(current)
        chunks = chunks or [cleaned_text]
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        pcm_chunks = []
        for chunk in chunks:
            prompt = f"{style} Perform this Egyptian Arabic script exactly as written. Do not translate, summarize, or add words: {chunk}"
            audio_directive = f"Performance direction: {style}. Speak in natural Egyptian Arabic. Recite the script verbatim, with no translation, summary, or additions. Script: {chunk}"
            response = client.models.generate_content(
                model=Config.GOOGLE_TTS_MODEL,
                contents=audio_directive,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_info["id"])
                        )
                    ),
                ),
            )
            part = response.candidates[0].content.parts[0]
            audio_bytes = part.inline_data.data
            mime_type = (part.inline_data.mime_type or "audio/pcm").lower()
            if isinstance(audio_bytes, str):
                import base64
                audio_bytes = base64.b64decode(audio_bytes)
            pcm_chunks.append(audio_bytes[44:] if "wav" in mime_type and audio_bytes[:4] == b"RIFF" else audio_bytes)
        if not pcm_chunks:
            raise RuntimeError("Gemini returned no audio chunks.")
        output_path.write_bytes(self._pcm_to_wav(b"".join(pcm_chunks)))
        return "wav"

    def generate_voiceover(self, idea_id, text, voice_key="shakir", output_dir=None, rate="+0%", video_type="Short-form"):
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

        use_google = voice_key in GOOGLE_VOICES
        extension = "wav" if use_google else "mp3"
        filename = f"voiceover_{idea_id}_{voice_key}.{extension}"
        output_path = output_dir / filename

        # Run edge-tts synthesis safely across sync and async contexts
        try:
            if use_google:
                extension = self._synthesize_gemini(text, voice_key, video_type, output_path)
            else:
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
            "provider": "Google Gemini TTS" if use_google else "Edge TTS",
            "format": extension.upper(),
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
