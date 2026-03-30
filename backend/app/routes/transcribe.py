"""NeuroNote AI - Transcription Routes"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.services.whisper_service import transcribe_audio

router = APIRouter()


@router.post("/transcribe")
async def transcribe_endpoint(
    audio: UploadFile = File(...),
):
    """
    Transcribe uploaded audio file using Whisper.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    try:
        audio_bytes = await audio.read()
        result = await transcribe_audio(audio_bytes, filename=audio.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
