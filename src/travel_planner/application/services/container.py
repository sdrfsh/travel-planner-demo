"""Services: all use cases in one object, built once by the composition root (server.py)."""

from dataclasses import dataclass

from travel_planner.application.services.create_trip_service import CreateTripService
from travel_planner.application.services.get_trip_service import GetTripService
from travel_planner.application.services.list_trips_service import ListTripsService
from travel_planner.application.services.search_memory_service import (
    SearchMemoryService,
)


@dataclass(frozen=True)
class Services:
    create_trip: CreateTripService
    get_trip: GetTripService
    list_trips: ListTripsService
    search_memory: SearchMemoryService
