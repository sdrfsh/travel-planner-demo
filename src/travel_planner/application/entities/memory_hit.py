"""MemoryHit: one note chunk returned by a travel memory search."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryHit:
    id: str
    text: str
    source: str | None
    section: str | None
    city: str | None
    country: str | None
    score: float  # cosine similarity: higher = closer
