"""NeuroNote AI - Notes Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.database import get_db
from app.models.note import Note
from app.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse, StructureRequest, StructuredNoteResponse
from app.services.llm_service import structure_notes
from app.services.file_parsing import extract_text_from_upload

router = APIRouter()

# 5 MB upload ceiling to avoid huge payloads overwhelming the service
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


@router.post("/notes/structure", response_model=StructuredNoteResponse)
async def structure_transcript(request: StructureRequest):
    """
    Send raw transcript to LLM to get structured notes.
    """
    try:
        structured_data = await structure_notes(
            transcript=request.transcript,
            custom_prompt=request.custom_prompt
        )
        return structured_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structuring failed: {str(e)}")


@router.post("/notes", response_model=NoteResponse)
async def create_note(note_in: NoteCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new structured note in the database.
    """
    new_note = Note(
        title=note_in.title,
        raw_transcript=note_in.raw_transcript,
        structured_notes=note_in.structured_notes,
        summary=note_in.summary,
        bullet_points=note_in.bullet_points,
        headings=note_in.headings,
        mind_map=note_in.mind_map,
        tags=note_in.tags,
        used_fallback=note_in.used_fallback,
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note


@router.post("/notes/upload", response_model=NoteResponse)
async def upload_note_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a text or docx file, structure it, and save as a note."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".txt", ".docx"}:
        raise HTTPException(status_code=400, detail="Only .txt and .docx files are supported")

    try:
        raw_bytes = await file.read()
        if len(raw_bytes) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Max 5 MB.")
        transcript_text = extract_text_from_upload(raw_bytes, ext)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    if not transcript_text or not transcript_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        structured_data = await structure_notes(transcript=transcript_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Structuring failed: {exc}")

    new_note = Note(
        title=structured_data.get("title") or "Untitled Note",
        raw_transcript=transcript_text,
        structured_notes=structured_data.get("structured_notes") or "",
        summary=structured_data.get("summary"),
        bullet_points=structured_data.get("bullet_points"),
        headings=structured_data.get("headings"),
        mind_map=structured_data.get("mind_map"),
        tags=structured_data.get("tags"),
        used_fallback=structured_data.get("used_fallback", False),
    )

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note


@router.get("/notes", response_model=NoteListResponse)
async def get_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of all notes.
    """
    stmt = select(Note).order_by(Note.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    notes = result.scalars().all()
    
    count_stmt = select(Note.id)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return {"notes": notes, "total": total}


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific note by ID.
    """
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    return note


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, note_in: NoteUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update a specific note by ID.
    """
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    update_data = note_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)
        
    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a specific note by ID.
    """
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    await db.delete(note)
    await db.commit()
    return {"message": "Note deleted successfully"}
