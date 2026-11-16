"""Tests for config.Settings: where every path ends up."""

from pathlib import Path

import pytest

from travel_planner.infrastructure.config import REPO_ROOT, Settings

PATH_VARS = ["DATA_DIR", "DB_PATH", "QDRANT_PATH", "NOTES_DIR", "EVAL_PATH"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove path env vars so the real machine's settings can't leak into tests."""
    for name in PATH_VARS:
        monkeypatch.delenv(name, raising=False)


def make_settings() -> Settings:
    """Build Settings without reading the repo's real .env file."""
    return Settings(_env_file=None)


def test_repo_root_is_the_repo() -> None:
    assert (REPO_ROOT / "pyproject.toml").is_file()


def test_defaults_live_in_repo_data_dir() -> None:
    settings = make_settings()

    data_dir = REPO_ROOT / "data"
    assert settings.data_dir == data_dir
    assert settings.db_path == data_dir / "trips.db"
    assert settings.qdrant_path == data_dir / "qdrant"
    assert settings.notes_dir == data_dir / "notes"
    assert settings.eval_path == data_dir / "eval.yaml"


def test_data_dir_moves_every_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    settings = make_settings()

    assert settings.db_path == tmp_path / "trips.db"
    assert settings.qdrant_path == tmp_path / "qdrant"
    assert settings.notes_dir == tmp_path / "notes"


def test_explicit_path_wins_over_data_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom_db = tmp_path / "elsewhere" / "my.db"
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DB_PATH", str(custom_db))

    settings = make_settings()

    assert settings.db_path == custom_db
    assert settings.notes_dir == tmp_path / "notes"  # others still follow DATA_DIR
