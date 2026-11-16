"""Tests for the use cases, with in-memory fakes (no database, no Qdrant, no model)."""

import pytest

from travel_planner.application.errors import InvalidInputError, NotFoundError
from travel_planner.application.services import MAX_TOP_K


def test_create_trip_stores_and_returns_it(services) -> None:
    trip = services.create_trip.invoke(
        "Porto", "2030-06-01", "2030-06-05", interests=["food"]
    )

    assert trip.id == 1
    assert trip.interests == ("food",)
    assert services.get_trip.invoke(1) == trip


def test_create_trip_with_bad_dates_stores_nothing(services, trip_repo) -> None:
    with pytest.raises(InvalidInputError):
        services.create_trip.invoke("Porto", "2030-06-05", "2030-06-01")

    assert trip_repo.trips == {}


def test_unknown_trip_names_the_recovery_tool(services) -> None:
    with pytest.raises(NotFoundError, match="Run list_trips"):
        services.get_trip.invoke(999)


def test_list_trips_sorted_by_start_date(services) -> None:
    services.create_trip.invoke("Later", "2031-01-01", "2031-01-02")
    services.create_trip.invoke("Sooner", "2030-01-01", "2030-01-02")

    assert [t.destination for t in services.list_trips.invoke()] == ["Sooner", "Later"]


@pytest.mark.parametrize("top_k", [0, MAX_TOP_K + 1])
def test_top_k_outside_range_is_rejected(services, top_k: int) -> None:
    with pytest.raises(InvalidInputError, match="top_k"):
        services.search_memory.invoke("cafes", top_k)


def test_memory_search_returns_hits(services) -> None:
    assert services.search_memory.invoke("pasta", 3)[0].source == "rome-2025.md"


def test_city_filter_is_passed_on_and_blank_means_all(services, memory) -> None:
    services.search_memory.invoke("cafes", 3, city=" Vienna ")
    services.search_memory.invoke("cafes", 3, city="  ")

    assert memory.calls == [("cafes", 3, "Vienna"), ("cafes", 3, None)]
