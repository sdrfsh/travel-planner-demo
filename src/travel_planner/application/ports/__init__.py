"""Ports: what the application needs from the outside world, one file each.

Infrastructure adapters implement these (SQLite, Qdrant, ...).
Tests implement them with in-memory fakes.
"""

from travel_planner.application.ports.memory_search import MemorySearch
from travel_planner.application.ports.trip_repository import TripRepository

__all__ = ["MemorySearch", "TripRepository"]
