"""Trip: a trip and the rule that belongs to it."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from travel_planner.application.errors import InvalidInputError

TravelType = Literal["relaxed", "packed"]


@dataclass(frozen=True)
class Trip:
    """A trip. `id` is None until a repository has stored it."""

    destination: str
    start_date: date
    end_date: date
    travel_type: TravelType = "relaxed"
    interests: tuple[str, ...] | None = None
    budget: int | None = None
    currency: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise InvalidInputError(
                f"end_date {self.end_date} is before start_date {self.start_date}. "
                "Check the dates with the user."
            )
