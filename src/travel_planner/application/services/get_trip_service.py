"""GetTripService: read one trip by id."""

from travel_planner.application.entities import Trip
from travel_planner.application.errors import NotFoundError
from travel_planner.application.ports import TripRepository


class GetTripService:
    def __init__(self, repo: TripRepository) -> None:
        self.repo = repo

    def invoke(self, trip_id: int) -> Trip:
        """Return the trip. Raises NotFoundError if it doesn't exist."""
        trip = self.repo.get(trip_id)
        if trip is None:
            raise NotFoundError(
                f"No trip found with id {trip_id}. Run list_trips and find the correct trip_id."
            )
        return trip
