"""MCP adapter: turns the application's use cases into MCP tools, a resource and a prompt.

Thin layer only: no rules here. Its two jobs:
- shape data for MCP (Trip -> dict with ISO dates)
- turn application errors into the MCP error type whose message gets through
  (the SDK hides the text of any other exception):
    tools     -> ToolError     (result with isError: true; Claude reads it)
    resources -> ResourceError (JSON-RPC error with the message)
"""

import json
from dataclasses import asdict
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from pydantic import Field

from travel_planner.application.entities import TravelType, Trip
from travel_planner.application.errors import InvalidInputError, TravelPlannerError
from travel_planner.application.services import MAX_TOP_K, Services

SUMMARIZE_CITY_TEMPLATE = """\
Summarize my own experience of {city} from my travel notes.

1. Call search_my_travel_memory with city="{city}" (top_k 10) and, if useful,
   a few more targeted queries (food, cafes, sights).
2. Group what you find into: loved, liked, disliked/hated. One line per place,
   with why, and cite its source as [file#section].
3. End with 2-3 tips I wrote for {city}.
Use only my notes. If they say nothing about something, say so.
"""


def trip_to_dict(trip: Trip) -> dict:
    """Trip -> JSON-friendly dict: id first, dates as YYYY-MM-DD, interests as a list."""
    data = {"id": trip.id, **asdict(trip)}
    data["start_date"] = trip.start_date.isoformat()
    data["end_date"] = trip.end_date.isoformat()
    data["interests"] = list(trip.interests) if trip.interests is not None else None
    return data


def parse_trip_id(trip_id: str) -> int:
    """Resource URIs arrive as text; turn one into a trip id."""
    try:
        return int(trip_id)
    except ValueError:
        raise InvalidInputError(
            f"trip_id must be a number, got {trip_id!r}. Run list_trips to find the correct trip_id."
        ) from None


def create_mcp(services: Services) -> MCPServer:
    """Build the MCP server: register every tool, the resource and the prompt."""
    mcp = MCPServer("travel-planner-demo")

    @mcp.tool()
    def create_trip(
        destination: Annotated[str, Field(description="City or country, e.g. 'Rome'.")],
        start_date: Annotated[str, Field(description="First day, YYYY-MM-DD.")],
        end_date: Annotated[
            str, Field(description="Last day, YYYY-MM-DD, on or after start_date.")
        ],
        travel_type: Annotated[
            TravelType,
            Field(
                description="'relaxed' = few stops a day, 'packed' = many stops a day."
            ),
        ] = "relaxed",
        interests: Annotated[
            list[str] | None,
            Field(description="What this trip is about, e.g. ['food', 'viewpoints']."),
        ] = None,
        budget: Annotated[
            int | None, Field(ge=0, description="Budget amount, in `currency`.")
        ] = None,
        currency: Annotated[
            str | None,
            Field(pattern=r"^[A-Z]{3}$", description="3-letter ISO code, e.g. EUR."),
        ] = None,
    ) -> dict:
        """Create a new trip and save it.

        Returns the saved trip, including its new id (use it with get_trip).
        """
        try:
            trip = services.create_trip.invoke(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                travel_type=travel_type,
                interests=interests,
                budget=budget,
                currency=currency,
            )
        except TravelPlannerError as e:
            raise ToolError(str(e)) from e
        return trip_to_dict(trip)

    @mcp.tool()
    def get_trip(
        trip_id: Annotated[int, Field(description="The trip's id, from list_trips.")],
    ) -> dict:
        """Get one trip: destination, dates, travel_type, interests, budget, currency.

        If you don't know the id, call list_trips first.
        """
        try:
            return trip_to_dict(services.get_trip.invoke(trip_id))
        except TravelPlannerError as e:
            raise ToolError(str(e)) from e

    @mcp.tool()
    def list_trips() -> list[dict]:
        """List all the user's trips with their ids, sorted by start date.

        Use an id from here with get_trip.
        """
        return [trip_to_dict(trip) for trip in services.list_trips.invoke()]

    @mcp.tool()
    def search_my_travel_memory(
        query: Annotated[
            str,
            Field(
                description="What to look for, e.g. 'cafes I loved' or 'quiet viewpoints'."
            ),
        ],
        top_k: Annotated[
            int,
            Field(
                ge=1,
                le=MAX_TOP_K,
                description=f"How many notes to return (1-{MAX_TOP_K}).",
            ),
        ] = 5,
        city: Annotated[
            str | None,
            Field(
                description="Only search notes from this city, e.g. 'Rome'. Omit for all."
            ),
        ] = None,
    ) -> list[dict]:
        """Search the user's own travel memory: personal notes from their past trips.

        Use this for questions about places the user has visited and what they
        thought of them (loved, liked, disliked, hated, and why), their tips, and
        their travel taste, e.g. "what did I love in Rome?" or "what kinds of
        places do I enjoy?". Do not use it for general facts about a destination.

        Returns matching note chunks, best match first. Each has id, text, source
        (note file), section (heading), city, country and score (higher = closer).
        Always cite the source and section in your answer. If no chunk is
        relevant, say so instead of guessing.
        """
        try:
            return [
                asdict(hit) for hit in services.search_memory.invoke(query, top_k, city)
            ]
        except TravelPlannerError as e:
            raise ToolError(str(e)) from e

    @mcp.resource("trip://{trip_id}", mime_type="application/json")
    def trip_resource(trip_id: str) -> str:
        """One trip as JSON, e.g. trip://1 (ids come from list_trips)."""
        try:
            trip = services.get_trip.invoke(parse_trip_id(trip_id))
        except TravelPlannerError as e:
            raise ResourceError(str(e)) from e
        return json.dumps(trip_to_dict(trip), indent=2, ensure_ascii=False)

    @mcp.prompt()
    def summarize_city(
        city: Annotated[
            str, Field(description="A city from my travel notes, e.g. Rome.")
        ],
    ) -> str:
        """Summarize what I loved and disliked in a city, from my own notes, with sources."""
        return SUMMARIZE_CITY_TEMPLATE.format(city=city.strip())

    return mcp
