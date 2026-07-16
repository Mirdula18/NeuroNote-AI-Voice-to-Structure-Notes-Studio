"""NeuroNote AI - Pydantic Schemas"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# --- Transcription ---

class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None


# --- Note Structuring ---

class StructureRequest(BaseModel):
    transcript: str


class StructuredNoteResponse(BaseModel):
    title: str
    structured_notes: str
    summary: str
    bullet_points: List[str]
    headings: List[str]
    mind_map: Dict[str, Any]
    tags: List[str]
    used_fallback: bool = False


# --- Notes CRUD ---

class NoteCreate(BaseModel):
    title: str
    raw_transcript: str
    structured_notes: str
    summary: Optional[str] = None
    bullet_points: Optional[List[str]] = None
    headings: Optional[List[str]] = None
    mind_map: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = []
    used_fallback: bool = False


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    structured_notes: Optional[str] = None
    summary: Optional[str] = None
    bullet_points: Optional[List[str]] = None
    headings: Optional[List[str]] = None
    mind_map: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    used_fallback: Optional[bool] = None


class NoteResponse(BaseModel):
    id: int
    title: str
    raw_transcript: str
    structured_notes: str
    summary: Optional[str]
    bullet_points: Optional[List[str]]
    headings: Optional[List[str]]
    mind_map: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    used_fallback: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    notes: List[NoteResponse]
    total: int
