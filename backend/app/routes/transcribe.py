"""NeuroNote AI - Transcription Routes"""

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.whisper_service import transcribe_audio

router = APIRouter()

MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/transcribe")
async def transcribe_endpoint(
    audio: UploadFile = File(...),
):
    """
    Transcribe uploaded audio file using Whisper.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio file too large. Max 25 MB.")

    try:
        result = await transcribe_audio(audio_bytes, filename=audio.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Transcription failed. Please try again.")
