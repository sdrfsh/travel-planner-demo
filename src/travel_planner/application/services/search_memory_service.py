"""SearchMemoryService: search my travel notes by meaning."""

from travel_planner.application.entities import MemoryHit
from travel_planner.application.errors import InvalidInputError
from travel_planner.application.ports import MemorySearch

MAX_TOP_K = 10  # more chunks add noise for Claude, not answers


class SearchMemoryService:
    def __init__(self, memory: MemorySearch) -> None:
        self.memory = memory

    def invoke(
        self, query: str, top_k: int = 5, city: str | None = None
    ) -> list[MemoryHit]:
        """Return the top_k closest notes. Raises InvalidInputError for a bad top_k."""
        if not 1 <= top_k <= MAX_TOP_K:
            raise InvalidInputError(
                f"top_k must be between 1 and {MAX_TOP_K}, got {top_k}."
            )
        city = city.strip() if city else None
        return self.memory.search(query, top_k, city=city or None)
