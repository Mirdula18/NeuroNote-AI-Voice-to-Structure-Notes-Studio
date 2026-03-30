"""NeuroNote AI - LLM Service for Note Structuring via Ollama"""

import json
import logging
import httpx
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

STRUCTURE_PROMPT = """You are NeuroNote AI, an expert at converting raw speech transcripts into beautifully structured notes.

Given the following raw transcript from a voice recording, produce a well-organized, structured output.

TRANSCRIPT:
\"\"\"
{transcript}
\"\"\"

You MUST return a valid JSON object with exactly these keys:
{{
  "title": "A concise, descriptive title for the note",
  "structured_notes": "Full structured notes in Markdown format with headings (##), bullet points, and paragraphs",
  "summary": "A 2-4 sentence summary of the key points",
  "bullet_points": ["Key point 1", "Key point 2", "Key point 3", ...],
  "headings": ["Main Topic 1", "Main Topic 2", ...],
  "mind_map": {{
    "id": "root",
    "label": "Main Topic",
    "children": [
      {{
        "id": "1",
        "label": "Subtopic 1",
        "children": [
          {{"id": "1.1", "label": "Detail 1", "children": []}},
          {{"id": "1.2", "label": "Detail 2", "children": []}}
        ]
      }},
      {{
        "id": "2",
        "label": "Subtopic 2",
        "children": []
      }}
    ]
  }},
  "tags": ["tag1", "tag2", "tag3"]
}}

RULES:
- The structured_notes should use proper Markdown formatting
- Bullet points should be the key takeaways
- The mind map should capture the hierarchical structure of ideas
- Tags should be relevant keywords
- Keep the summary concise but informative
- Fix any grammar or speech artifacts from the transcript
- Return ONLY the JSON object, no other text"""


async def structure_notes(transcript: str, custom_prompt: Optional[str] = None) -> dict:
    """
    Send transcript to Ollama LLM and get structured notes back.

    Args:
        transcript: Raw transcript text
        custom_prompt: Optional custom prompt to override default

    Returns:
        Structured notes dictionary
    """
    if not transcript or not transcript.strip():
        return _empty_response()

    prompt = custom_prompt or STRUCTURE_PROMPT.format(transcript=transcript)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 4096,
                    },
                    "format": "json",
                },
            )
            response.raise_for_status()
            result = response.json()

        generated = result.get("response", "")
        logger.info(f"LLM response length: {len(generated)} chars")

        # Parse JSON from response
        parsed = _parse_llm_json(generated)
        result = _validate_structure(parsed)
        result["used_fallback"] = False
        return result

    except httpx.ConnectError:
        logger.error("Cannot connect to Ollama. Is it running?")
        return _fallback_structure(transcript)
    except Exception as e:
        logger.error(f"LLM structuring failed: {e}")
        return _fallback_structure(transcript)


def _parse_llm_json(text: str) -> dict:
    """Try to parse JSON from LLM output, handling common issues."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown code fences
    import re
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object
    brace_start = text.find("{")
    brace_end = text.rfind("}") + 1
    if brace_start != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")


def _validate_structure(data: dict) -> dict:
    """Ensure LLM output has all required fields."""
    defaults = {
        "title": "Untitled Note",
        "structured_notes": "",
        "summary": "",
        "bullet_points": [],
        "headings": [],
        "mind_map": {"id": "root", "label": "Note", "children": []},
        "tags": [],
        "used_fallback": False,
    }
    for key, default in defaults.items():
        if key not in data:
            data[key] = default
    return data


def _fallback_structure(transcript: str) -> dict:
    """Generate basic structure when LLM is unavailable."""
    sentences = [s.strip() for s in transcript.split(".") if s.strip()]
    title = sentences[0][:100] if sentences else "Untitled Note"
    bullet_points = sentences[:10]

    return {
        "title": title,
        "structured_notes": f"## Notes\n\n{transcript}",
        "summary": transcript[:300] + ("..." if len(transcript) > 300 else ""),
        "bullet_points": bullet_points,
        "headings": ["Notes"],
        "mind_map": {
            "id": "root",
            "label": title[:50],
            "children": [
                {"id": str(i + 1), "label": bp[:60], "children": []}
                for i, bp in enumerate(bullet_points[:5])
            ],
        },
        "tags": [],
        "used_fallback": True,
    }


def _empty_response() -> dict:
    return {
        "title": "Empty Note",
        "structured_notes": "",
        "summary": "",
        "bullet_points": [],
        "headings": [],
        "mind_map": {"id": "root", "label": "Empty", "children": []},
        "tags": [],
        "used_fallback": False,
    }
