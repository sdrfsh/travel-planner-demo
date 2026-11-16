"""CreateTripService: validate input and store a new trip."""

from travel_planner.application.entities import TravelType, Trip
from travel_planner.application.helpers import parse_date
from travel_planner.application.ports import TripRepository


class CreateTripService:
    def __init__(self, repo: TripRepository) -> None:
        self.repo = repo

    def invoke(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        travel_type: TravelType = "relaxed",
        interests: list[str] | None = None,
        budget: int | None = None,
        currency: str | None = None,
    ) -> Trip:
        """Return the stored trip with its new id. Raises InvalidInputError."""
        trip = Trip(
            destination=destination,
            start_date=parse_date(start_date, "start_date"),
            end_date=parse_date(end_date, "end_date"),
            travel_type=travel_type,
            interests=tuple(interests) if interests is not None else None,
            budget=budget,
            currency=currency,
        )
        return self.repo.add(trip)
