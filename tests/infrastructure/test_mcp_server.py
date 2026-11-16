"""Tests for the MCP adapter: data shape, and errors reaching the client with their message."""

import asyncio
import json

import pytest
from mcp.server.mcpserver.exceptions import ResourceError, ToolError

from travel_planner.application.services import MAX_TOP_K
from travel_planner.infrastructure.mcp_server import create_mcp
from travel_planner.server import build_server


def call_tool(mcp, name: str, arguments: dict):
    return asyncio.run(mcp.call_tool(name, arguments))


def call_json(mcp, name: str, arguments: dict):
    """Call a tool and decode the JSON text Claude would receive."""
    return json.loads(call_tool(mcp, name, arguments).content[0].text)


@pytest.fixture
def mcp(services):
    return create_mcp(services)


def test_create_trip_returns_iso_dates_and_list(mcp) -> None:
    args = {
        "destination": "Porto",
        "start_date": "2030-06-01",
        "end_date": "2030-06-05",
        "interests": ["food"],
    }

    trip = call_json(mcp, "create_trip", args)

    assert trip["id"] == 1
    assert trip["start_date"] == "2030-06-01"
    assert trip["interests"] == ["food"]


def test_unknown_trip_reaches_claude_with_its_hint(mcp) -> None:
    with pytest.raises(ToolError, match="Run list_trips"):
        call_tool(mcp, "get_trip", {"trip_id": 999})


def test_bad_dates_reach_claude_with_the_format(mcp) -> None:
    args = {
        "destination": "Porto",
        "start_date": "01.06.2030",
        "end_date": "2030-06-05",
    }
    with pytest.raises(ToolError, match="YYYY-MM-DD"):
        call_tool(mcp, "create_trip", args)


def test_empty_memory_reaches_claude(mcp, memory) -> None:
    memory.hits = []

    with pytest.raises(ToolError, match="memory is empty"):
        call_tool(mcp, "search_my_travel_memory", {"query": "cafes"})


def test_top_k_above_limit_is_rejected_by_the_schema(mcp) -> None:
    with pytest.raises(ToolError, match="top_k"):
        call_tool(
            mcp, "search_my_travel_memory", {"query": "cafes", "top_k": MAX_TOP_K + 1}
        )


def test_search_with_city_filter(mcp) -> None:
    result = call_tool(
        mcp, "search_my_travel_memory", {"query": "cafes", "city": "Vienna"}
    )

    hits = [json.loads(block.text) for block in result.content]
    assert [h["city"] for h in hits] == ["Vienna"]


def test_trip_resource_returns_json(mcp, services) -> None:
    trip = services.create_trip.invoke("Porto", "2030-06-01", "2030-06-05")

    contents = asyncio.run(mcp.read_resource(f"trip://{trip.id}"))

    assert json.loads(contents[0].content)["destination"] == "Porto"


@pytest.mark.parametrize("uri", ["trip://999", "trip://abc"])
def test_bad_trip_resource_reaches_the_client(mcp, uri: str) -> None:
    with pytest.raises(ResourceError, match="list_trips"):
        asyncio.run(mcp.read_resource(uri))


def test_summarize_city_prompt_uses_the_city_filter(mcp) -> None:
    result = asyncio.run(mcp.get_prompt("summarize_city", {"city": "Rome"}))

    text = result.messages[0].content.text
    assert 'city="Rome"' in text
    assert "[file#section]" in text


def test_real_wiring_creates_and_reads_a_trip(tmp_settings, memory) -> None:
    """The composition root wires SQLite + MCP correctly (temp folder; fake memory)."""
    mcp = build_server(tmp_settings, memory=memory)
    args = {
        "destination": "Ghent",
        "start_date": "2030-03-01",
        "end_date": "2030-03-04",
    }

    created = call_json(mcp, "create_trip", args)
    fetched = call_json(mcp, "get_trip", {"trip_id": created["id"]})

    assert fetched == created
    assert tmp_settings.db_path.is_file()
