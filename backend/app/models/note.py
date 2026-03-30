"""NeuroNote AI - Note Database Model"""

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, default="Untitled Note")
    raw_transcript = Column(Text, nullable=False)
    structured_notes = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    bullet_points = Column(JSON, nullable=True)
    headings = Column(JSON, nullable=True)
    mind_map = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True, default=[])
    used_fallback = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "raw_transcript": self.raw_transcript,
            "structured_notes": self.structured_notes,
            "summary": self.summary,
            "bullet_points": self.bullet_points,
            "headings": self.headings,
            "mind_map": self.mind_map,
            "tags": self.tags,
            "used_fallback": self.used_fallback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
