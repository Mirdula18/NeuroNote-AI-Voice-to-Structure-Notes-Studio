"""NeuroNote AI - Export Routes"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.database import get_db
from app.models.note import Note

router = APIRouter()


@router.get("/export/{note_id}/markdown")
async def export_markdown(note_id: int, db: AsyncSession = Depends(get_db)):
    """
    Export a note as a Markdown file.
    """
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    content = f"# {note.title}\n\n"
    content += f"**Date:** {note.created_at.strftime('%Y-%m-%d %H:%M:%S') if note.created_at else 'Unknown'}\n"
    if note.tags:
        content += f"**Tags:** {', '.join(note.tags)}\n"
    
    content += f"\n## Summary\n{note.summary or 'No summary available.'}\n\n"
    
    if note.bullet_points:
        content += "## Key Points\n"
        for bp in note.bullet_points:
            content += f"- {bp}\n"
        content += "\n"
        
    content += f"---\n\n{note.structured_notes}\n"
    
    filename = f"{note.title[:20].replace(' ', '_')}_{note.id}.md"
    
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/{note_id}/json")
async def export_json(note_id: int, db: AsyncSession = Depends(get_db)):
    """
    Export a note as a complete JSON structure.
    """
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    note_dict = note.to_dict()
    
    filename = f"{note.title[:20].replace(' ', '_')}_{note.id}.json"
    
    return Response(
        content=json.dumps(note_dict, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
