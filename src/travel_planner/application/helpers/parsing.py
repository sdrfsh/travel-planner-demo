"""Turning raw input (text from MCP or a web form) into values the entities use."""

from datetime import date, datetime

from travel_planner.application.errors import InvalidInputError

DATE_FORMAT = "%Y-%m-%d"


def parse_date(value: str, field: str) -> date:
    """Parse a YYYY-MM-DD string. Raises InvalidInputError naming the field."""
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise InvalidInputError(
            f"{field} must be a date in YYYY-MM-DD format (e.g. 2027-03-15), got {value!r}."
        ) from None
