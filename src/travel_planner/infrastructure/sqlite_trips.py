"""TripRepository on SQLite."""

import json
import logging
import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date
from pathlib import Path

from travel_planner.application.entities import Trip

logger = logging.getLogger(__name__)

SCHEMA = """
    CREATE TABLE IF NOT EXISTS trips(
        id INTEGER PRIMARY KEY,
        destination TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        travel_type TEXT NOT NULL DEFAULT 'relaxed',
        interests TEXT,
        budget INTEGER,
        currency TEXT
    )
    """


class SqliteTripRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def create_schema(self) -> None:
        """Create the database folder and the trips table if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as con:
            with con:  # commits on success
                con.execute(SCHEMA)
        logger.info(f"DB is ready at {self.db_path}")

    def add(self, trip: Trip) -> Trip:
        sql = """
            INSERT INTO trips (destination, start_date, end_date, travel_type, interests, budget, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        interests = (
            json.dumps(list(trip.interests)) if trip.interests is not None else None
        )
        values = (
            trip.destination,
            trip.start_date.isoformat(),
            trip.end_date.isoformat(),
            trip.travel_type,
            interests,
            trip.budget,
            trip.currency,
        )
        with closing(self._connect()) as con:
            with con:
                new_id = con.execute(sql, values).lastrowid
        logger.info(f"Trip {new_id} created")
        return replace(trip, id=new_id)

    def get(self, trip_id: int) -> Trip | None:
        with closing(self._connect()) as con:
            row = con.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        return _row_to_trip(row) if row is not None else None

    def list_all(self) -> list[Trip]:
        with closing(self._connect()) as con:
            rows = con.execute("SELECT * FROM trips ORDER BY start_date").fetchall()
        return [_row_to_trip(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con


def _row_to_trip(row: sqlite3.Row) -> Trip:
    """DB row -> Trip: ISO text -> date, interests JSON text -> tuple (NULL stays None)."""
    interests = json.loads(row["interests"]) if row["interests"] is not None else None
    return Trip(
        id=row["id"],
        destination=row["destination"],
        start_date=date.fromisoformat(row["start_date"]),
        end_date=date.fromisoformat(row["end_date"]),
        travel_type=row["travel_type"],
        interests=tuple(interests) if interests is not None else None,
        budget=row["budget"],
        currency=row["currency"],
    )
