"""TripRepository: where trips are stored."""

from typing import Protocol

from travel_planner.application.entities import Trip


class TripRepository(Protocol):
    def add(self, trip: Trip) -> Trip:
        """Store a new trip and return it with its id."""
        ...

    def get(self, trip_id: int) -> Trip | None:
        """Return the trip, or None if there is no trip with this id."""
        ...

    def list_all(self) -> list[Trip]:
        """Return all trips, sorted by start date."""
        ...
