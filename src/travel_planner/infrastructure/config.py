"""All paths in one place.

Order of precedence: real environment variables > the repo's .env file > defaults.
Every path defaults to a location inside DATA_DIR (repo-root data/ by default).
"""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = (
    Path(__file__).resolve().parents[3]
)  # src/travel_planner/infrastructure/ -> repo


class Settings(BaseSettings):
    """Paths the app needs. Env var names are the field names in upper case."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    data_dir: Path = REPO_ROOT / "data"
    db_path: Path | None = None
    qdrant_path: Path | None = None
    notes_dir: Path | None = None
    eval_path: Path | None = None

    @model_validator(mode="after")
    def fill_defaults(self) -> "Settings":
        """Paths that are not set explicitly live inside data_dir."""
        self.db_path = self.db_path or self.data_dir / "trips.db"
        self.qdrant_path = self.qdrant_path or self.data_dir / "qdrant"
        self.notes_dir = self.notes_dir or self.data_dir / "notes"
        self.eval_path = self.eval_path or self.data_dir / "eval.yaml"
        return self


@lru_cache
def get_settings() -> Settings:
    """Load the settings once per process (on first call, not on import)."""
    return Settings()
