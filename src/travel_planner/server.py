"""Composition root: the only module that knows both layers.

Builds the infrastructure adapters, hands them to the application's use cases,
wraps those in the MCP server and runs it over stdio.
Start: `uv run python -m travel_planner.server` (Claude Desktop, Inspector).
"""

import logging

from mcp.server import MCPServer

from travel_planner.application.ports import MemorySearch
from travel_planner.application.services import (
    CreateTripService,
    GetTripService,
    ListTripsService,
    SearchMemoryService,
    Services,
)
from travel_planner.infrastructure.config import Settings, get_settings
from travel_planner.infrastructure.embeddings import FastEmbedEmbedder
from travel_planner.infrastructure.mcp_server import create_mcp
from travel_planner.infrastructure.qdrant_memory import QdrantMemory
from travel_planner.infrastructure.sqlite_trips import SqliteTripRepository


def build_services(settings: Settings, memory: MemorySearch | None = None) -> Services:
    """Wire adapters into use cases. `memory` can be swapped (tests use a fake)."""
    if memory is None:
        memory = QdrantMemory(settings.qdrant_path, FastEmbedEmbedder())
    trip_repo = SqliteTripRepository(settings.db_path)
    trip_repo.create_schema()
    return Services(
        create_trip=CreateTripService(trip_repo),
        get_trip=GetTripService(trip_repo),
        list_trips=ListTripsService(trip_repo),
        search_memory=SearchMemoryService(memory),
    )


def build_server(
    settings: Settings | None = None, memory: MemorySearch | None = None
) -> MCPServer:
    """The fully wired MCP server (settings from env/.env unless given)."""
    return create_mcp(build_services(settings or get_settings(), memory))


def main() -> None:
    logging.basicConfig(level=logging.INFO)  # stderr: stdout belongs to stdio
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
