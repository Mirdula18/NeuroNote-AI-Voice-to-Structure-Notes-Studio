"""NeuroNote AI - Whisper Transcription Service (using faster-whisper)"""

from faster_whisper import WhisperModel
import tempfile
import os
import logging
import time
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Global model cache
_model = None


def get_whisper_model():
    """Load and cache the faster-whisper model."""
    global _model
    if _model is None:
        logger.info(f"Loading faster-whisper model: {settings.whisper_model}")
        _model = WhisperModel(
            settings.whisper_model,
            device="cpu",
            compute_type="int8",
        )
        logger.info("Faster-whisper model loaded successfully")
    return _model


async def transcribe_audio(audio_data: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe audio data using faster-whisper.

    Args:
        audio_data: Raw audio bytes
        filename: Original filename for extension detection

    Returns:
        dict with text, language, and duration
    """
    start_time = time.time()

    # Write audio to temp file
    suffix = Path(filename).suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        model = get_whisper_model()

        # Transcribe with faster-whisper
        segments_gen, info = model.transcribe(
            tmp_path,
            language=None,  # Auto-detect language
            task="transcribe",
        )

        # Collect segments (generator must be consumed)
        segments = []
        full_text_parts = []
        for seg in segments_gen:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })
            full_text_parts.append(seg.text.strip())

        full_text = " ".join(full_text_parts)
        elapsed = time.time() - start_time
        logger.info(f"Transcription completed in {elapsed:.2f}s")

        return {
            "text": full_text,
            "language": info.language,
            "duration": elapsed,
            "segments": segments,
        }
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
