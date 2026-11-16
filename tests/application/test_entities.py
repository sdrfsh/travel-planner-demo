"""Tests for the entities' rules and the date helper."""

from datetime import date

import pytest

from travel_planner.application.entities import Trip
from travel_planner.application.errors import InvalidInputError
from travel_planner.application.helpers import parse_date


def test_parse_date_reads_iso() -> None:
    assert parse_date("2030-06-01", "day") == date(2030, 6, 1)


@pytest.mark.parametrize("bad", ["01.06.2030", "2030/06/01", "June 1", ""])
def test_parse_date_names_field_and_format(bad: str) -> None:
    with pytest.raises(
        InvalidInputError, match="start_date must be a date in YYYY-MM-DD"
    ):
        parse_date(bad, "start_date")


def test_end_before_start_is_rejected() -> None:
    with pytest.raises(InvalidInputError, match="before start_date"):
        Trip("Porto", date(2030, 6, 5), date(2030, 6, 1))


def test_one_day_trip_is_allowed() -> None:
    assert Trip("Ghent", date(2026, 6, 1), date(2026, 6, 1)).start_date == date(
        2026, 6, 1
    )
