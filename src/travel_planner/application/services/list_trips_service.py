"""ListTripsService: all trips, sorted by start date."""

from travel_planner.application.entities import Trip
from travel_planner.application.ports import TripRepository


class ListTripsService:
    def __init__(self, repo: TripRepository) -> None:
        self.repo = repo

    def invoke(self) -> list[Trip]:
        return self.repo.list_all()
