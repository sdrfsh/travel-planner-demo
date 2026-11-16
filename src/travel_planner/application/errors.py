"""Errors the application raises on purpose.

Messages are written for the caller (Claude or a person) to act on.
Adapters translate them into their own error types (e.g. MCP's ToolError).
"""


class TravelPlannerError(Exception):
    """Base class: an expected failure with a helpful message."""


class NotFoundError(TravelPlannerError):
    """Something asked for by id doesn't exist."""


class InvalidInputError(TravelPlannerError):
    """The caller's input breaks a rule (bad date, end before start, ...)."""


class SetupError(TravelPlannerError):
    """The user's data isn't ready (e.g. an empty travel memory)."""
