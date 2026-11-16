"""Tests for the SQLite adapter: trips survive the round trip unchanged."""

from datetime import date
from pathlib import Path

import pytest

from travel_planner.application.entities import Trip
from travel_planner.infrastructure.sqlite_trips import SqliteTripRepository


@pytest.fixture
def repo(tmp_path: Path) -> SqliteTripRepository:
    repo = SqliteTripRepository(tmp_path / "sub" / "trips.db")  # folder is created
    repo.create_schema()
    return repo


def test_add_then_get_returns_the_same_trip(repo) -> None:
    trip = Trip(
        "Porto",
        date(2030, 6, 1),
        date(2030, 6, 5),
        travel_type="packed",
        interests=("food", "viewpoints"),
        budget=70,
        currency="EUR",
    )

    stored = repo.add(trip)

    assert stored.id == 1
    assert repo.get(1) == stored


def test_missing_interests_stay_none(repo) -> None:
    stored = repo.add(Trip("Ghent", date(2026, 3, 1), date(2026, 3, 4)))

    assert repo.get(stored.id).interests is None


def test_unknown_id_returns_none(repo) -> None:
    assert repo.get(999) is None


def test_list_all_sorted_by_start_date(repo) -> None:
    repo.add(Trip("Later", date(2027, 1, 1), date(2027, 1, 2)))
    repo.add(Trip("Sooner", date(2026, 1, 1), date(2026, 1, 2)))

    assert [t.destination for t in repo.list_all()] == ["Sooner", "Later"]


def test_create_schema_twice_is_safe(repo) -> None:
    repo.add(Trip("Ghent", date(2026, 3, 1), date(2026, 3, 4)))

    repo.create_schema()

    assert len(repo.list_all()) == 1
