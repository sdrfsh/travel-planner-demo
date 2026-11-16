"""Offline ingestion: trip notes (Markdown) -> chunks -> embeddings -> Qdrant.

Run after changing notes: `uv run python -m travel_planner.infrastructure.ingest`
"""

from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from travel_planner.infrastructure.config import get_settings

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_SECTION_RE = re.compile(r"^## +(.+?)\s*$", re.MULTILINE)
_NON_SLUG_RE = re.compile(r"[^a-z0-9]+")


def split_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    """Return (front_matter, body). Files without front matter get an empty dict."""
    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        return {}, raw
    front = yaml.safe_load(match.group(1)) or {}
    return front, raw[match.end() :]


def flat_metadata(meta: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Flat, filter-friendly values: no None; dates -> ISO text; lists -> "a, b"."""
    safe: dict[str, str | int | float | bool] = {}
    for key, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            safe[key] = value
        elif isinstance(value, dt.date):  # also covers datetime
            safe[key] = value.isoformat()
        elif isinstance(value, (list, tuple, set)):
            safe[key] = ", ".join(str(v) for v in value)
        else:
            safe[key] = json.dumps(value, default=str)
    return safe


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = _NON_SLUG_RE.sub("-", ascii_text.lower()).strip("-")
    return slug or "section"


def load_chunks(notes_dir: Path | None = None) -> list[dict[str, Any]]:
    """Read every .md note and return one chunk per "## " section.

    Each chunk is {"id", "text", "metadata"}. Text before the first "## "
    (the "# Title" line) is not emitted as a chunk.
    Uses the configured notes folder unless notes_dir is given.
    """
    notes_dir = notes_dir or get_settings().notes_dir
    if not notes_dir.is_dir():
        raise FileNotFoundError(f"Notes directory not found: {notes_dir}")
    paths = sorted(notes_dir.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"No .md files in notes directory: {notes_dir}")

    chunks: list[dict[str, Any]] = []
    for path in paths:
        # utf-8-sig strips a BOM (common from Windows editors) so "---" front matter still matches
        front, body = split_front_matter(path.read_text(encoding="utf-8-sig"))
        country = front.get("country")
        if isinstance(country, (list, tuple)):
            country = ", ".join(str(c) for c in country)
        country_line = f"Country: {country}" if country else ""
        meta = flat_metadata(front)

        # split() with one capture group yields [preamble, heading, content, heading, content, ...]
        parts = _SECTION_RE.split(body)
        seen: dict[str, int] = {}
        for heading, content in zip(parts[1::2], parts[2::2], strict=True):
            content = content.strip()

            slug = slugify(heading)
            seen[slug] = seen.get(slug, 0) + 1
            if seen[slug] > 1:  # keep ids unique if a heading repeats in one file
                slug = f"{slug}-{seen[slug]}"

            chunks.append(
                {
                    "id": f"{path.stem}#{slug}",
                    "text": "\n".join(p for p in (heading, country_line, content) if p),
                    "metadata": {**meta, "source": path.name, "section": heading},
                }
            )
    return chunks


if __name__ == "__main__":
    from travel_planner.infrastructure.embeddings import FastEmbedEmbedder
    from travel_planner.infrastructure.qdrant_memory import QdrantMemory

    settings = get_settings()
    chunks = load_chunks(settings.notes_dir)
    memory = QdrantMemory(settings.qdrant_path, FastEmbedEmbedder())
    deleted = memory.sync(chunks)
    print(
        f"Synced {len(chunks)} chunks, deleted {deleted} orphans; Qdrant now has {memory.count()} points"
    )
