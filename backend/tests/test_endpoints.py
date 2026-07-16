"""Smoke tests for NeuroNote AI endpoints."""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient):
    res = await client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["service"] == "NeuroNote AI"
    assert body["status"] in ("ok", "degraded")
    assert "database" in body["components"]


# ---------------------------------------------------------------------------
# Notes CRUD
# ---------------------------------------------------------------------------

SAMPLE_NOTE = {
    "title": "Test Note",
    "raw_transcript": "Hello world, this is a test transcript.",
    "structured_notes": "## Test\n\nSome structured content.",
    "summary": "A short summary.",
    "bullet_points": ["Point 1", "Point 2"],
    "headings": ["Test"],
    "mind_map": {"id": "root", "label": "Test", "children": []},
    "tags": ["test"],
    "used_fallback": False,
}


@pytest.mark.asyncio
async def test_create_note(client: AsyncClient):
    res = await client.post("/api/notes", json=SAMPLE_NOTE)
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Test Note"
    assert body["id"] is not None


@pytest.mark.asyncio
async def test_list_notes(client: AsyncClient):
    await client.post("/api/notes", json=SAMPLE_NOTE)
    res = await client.get("/api/notes")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert len(body["notes"]) >= 1


@pytest.mark.asyncio
async def test_get_note_by_id(client: AsyncClient):
    create = await client.post("/api/notes", json=SAMPLE_NOTE)
    note_id = create.json()["id"]

    res = await client.get(f"/api/notes/{note_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "Test Note"


@pytest.mark.asyncio
async def test_get_note_not_found(client: AsyncClient):
    res = await client.get("/api/notes/99999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_note(client: AsyncClient):
    create = await client.post("/api/notes", json=SAMPLE_NOTE)
    note_id = create.json()["id"]

    res = await client.put(f"/api/notes/{note_id}", json={"title": "Updated Title"})
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient):
    create = await client.post("/api/notes", json=SAMPLE_NOTE)
    note_id = create.json()["id"]

    res = await client.delete(f"/api/notes/{note_id}")
    assert res.status_code == 200
    assert res.json()["message"] == "Note deleted successfully"

    # Verify it's gone
    res = await client.get(f"/api/notes/{note_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_note_not_found(client: AsyncClient):
    res = await client.delete("/api/notes/99999")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_markdown(client: AsyncClient):
    create = await client.post("/api/notes", json=SAMPLE_NOTE)
    note_id = create.json()["id"]

    res = await client.get(f"/api/export/{note_id}/markdown")
    assert res.status_code == 200
    assert "Test Note" in res.text
    assert res.headers["content-type"].startswith("text/markdown")


@pytest.mark.asyncio
async def test_export_json(client: AsyncClient):
    create = await client.post("/api/notes", json=SAMPLE_NOTE)
    note_id = create.json()["id"]

    res = await client.get(f"/api/export/{note_id}/json")
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Test Note"
    assert res.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_export_not_found(client: AsyncClient):
    res = await client.get("/api/export/99999/markdown")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Validation / Edge Cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_note_missing_fields(client: AsyncClient):
    res = await client.post("/api/notes", json={"title": "Only title"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_list_notes_pagination(client: AsyncClient):
    for i in range(3):
        await client.post("/api/notes", json={**SAMPLE_NOTE, "title": f"Note {i}"})

    res = await client.get("/api/notes?skip=0&limit=2")
    assert res.status_code == 200
    body = res.json()
    assert len(body["notes"]) == 2
    assert body["total"] == 3


@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient):
    res = await client.post(
        "/api/notes/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert res.status_code == 400
