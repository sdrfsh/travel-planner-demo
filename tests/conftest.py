"""Shared fixtures: in-memory fakes for the ports, a fake embedder, and temp settings."""

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from travel_planner.application.entities import MemoryHit, Trip
from travel_planner.application.errors import SetupError
from travel_planner.application.services import (
    CreateTripService,
    GetTripService,
    ListTripsService,
    SearchMemoryService,
    Services,
)
from travel_planner.infrastructure.config import Settings


class InMemoryTripRepository:
    """TripRepository fake: trips in a dict."""

    def __init__(self) -> None:
        self.trips: dict[int, Trip] = {}

    def add(self, trip: Trip) -> Trip:
        stored = replace(trip, id=len(self.trips) + 1)
        self.trips[stored.id] = stored
        return stored

    def get(self, trip_id: int) -> Trip | None:
        return self.trips.get(trip_id)

    def list_all(self) -> list[Trip]:
        return sorted(self.trips.values(), key=lambda t: t.start_date)


class FakeMemorySearch:
    """MemorySearch fake: returns `hits` (filtered by city); empty acts like an empty store."""

    def __init__(self) -> None:
        self.hits: list[MemoryHit] = [
            MemoryHit(
                "rome-2025#trattoria",
                "Trattoria",
                "rome-2025.md",
                "Trattoria",
                "Rome",
                "Italy",
                0.8,
            ),
            MemoryHit(
                "vienna-2024#cafe",
                "Cafe",
                "vienna-2024.md",
                "Cafe",
                "Vienna",
                "Austria",
                0.7,
            ),
        ]
        self.calls: list[tuple[str, int, str | None]] = []

    def search(
        self, query: str, top_k: int, city: str | None = None
    ) -> list[MemoryHit]:
        self.calls.append((query, top_k, city))
        if not self.hits:
            raise SetupError("The travel memory is empty")
        return [h for h in self.hits if city is None or h.city == city][:top_k]


class WordHashEmbedder:
    """Embedder fake: bag of words hashed into 64 numbers. Same words -> close vectors.

    Deterministic and offline, so tests can run real Qdrant (in memory) without a model.
    """

    dimension = 64

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for word in re.findall(r"[a-z]+", text.lower()):
            vector[
                int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dimension
            ] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


@pytest.fixture
def trip_repo() -> InMemoryTripRepository:
    return InMemoryTripRepository()


@pytest.fixture
def memory() -> FakeMemorySearch:
    return FakeMemorySearch()


@pytest.fixture
def services(trip_repo, memory) -> Services:
    """All use cases, wired to fakes: no database, no Qdrant, no model."""
    return Services(
        create_trip=CreateTripService(trip_repo),
        get_trip=GetTripService(trip_repo),
        list_trips=ListTripsService(trip_repo),
        search_memory=SearchMemoryService(memory),
    )


@pytest.fixture
def embedder() -> WordHashEmbedder:
    return WordHashEmbedder()


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    """Settings with every path in a temp folder; ignores my env vars and .env."""
    return Settings(
        _env_file=None,
        data_dir=tmp_path,
        db_path=tmp_path / "trips.db",
        qdrant_path=tmp_path / "qdrant",
        notes_dir=tmp_path / "notes",
        eval_path=tmp_path / "eval.yaml",
    )
