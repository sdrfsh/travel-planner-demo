"""MemorySearch: searching my travel notes by meaning."""

from typing import Protocol

from travel_planner.application.entities import MemoryHit


class MemorySearch(Protocol):
    def search(
        self, query: str, top_k: int, city: str | None = None
    ) -> list[MemoryHit]:
        """Return the top_k closest note chunks, best first (optionally only from `city`).

        Raises SetupError if no notes have been ingested.
        """
        ...
