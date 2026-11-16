# Layers

Two layers. Arrows mean "may import".

```
server.py  (composition root: the only place that knows both layers)
    │
    ▼
infrastructure/  adapters to the outside world
    │   incoming: mcp_server
    │   outgoing: sqlite_trips, qdrant_memory (+ embeddings), ingest, evaluate, config
    ▼
application/     plain Python: entities/, ports/, services/ (use cases), helpers/, errors
```

## Rules (checked by `uv run lint-imports`, also in CI)

1. `application` never imports `infrastructure` or `server`.
2. `application` never imports `mcp`, `qdrant_client`, `fastembed`, `pydantic`, `pydantic_settings`, `yaml` or `sqlite3`.
3. `infrastructure` never imports `server`.

## How a call flows: `get_trip(999)`

1. Claude calls the MCP tool `get_trip` → `infrastructure/mcp_server.py`
2. → `GetTripService.invoke` (use case) → `TripRepository.get` (port)
3. → `SqliteTripRepository.get` (adapter) returns `None`
4. The use case raises `NotFoundError("… Run list_trips …")` (application error)
5. The MCP adapter turns it into a `ToolError`, so Claude reads the message

## Why ports

A port is a `Protocol`: the list of methods the application needs.
Any class with those methods fits: SQLite and Qdrant here, Postgres or another
vector store tomorrow, an in-memory fake in tests (`tests/conftest.py`).
The use cases don't change.

## Use cases

One class per action, one file each, with a single `invoke()` method:
`CreateTripService`, `GetTripService`, `ListTripsService`, `SearchMemoryService`.
A use case gets its ports in `__init__`, so it does one thing and is easy to test.
