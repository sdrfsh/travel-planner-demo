"""Infrastructure layer: adapters to the outside world.

Outgoing (the app calls them): SQLite, Qdrant + FastEmbed, config.
Incoming (they call the app): the MCP server.
May import the application layer, never the other way round.
"""
