"""Tests for the Qdrant adapter: real Qdrant (in memory) with a fake, offline embedder."""

from pathlib import Path

import pytest

from travel_planner.application.errors import SetupError
from travel_planner.infrastructure.ingest import load_chunks
from travel_planner.infrastructure.qdrant_memory import QdrantMemory, point_id

SAMPLE_NOTES = Path(__file__).resolve().parents[2] / "examples" / "data" / "notes"


def chunk(chunk_id: str, text: str, city: str = "Rome") -> dict:
    return {
        "id": chunk_id,
        "text": text,
        "metadata": {"city": city, "source": f"{chunk_id}.md"},
    }


@pytest.fixture
def store(embedder) -> QdrantMemory:
    return QdrantMemory(None, embedder)  # None = in memory


def test_point_id_is_stable_uuid() -> None:
    assert point_id("rome#cafe") == point_id("rome#cafe")
    assert point_id("rome#cafe") != point_id("rome#bar")


def test_empty_store_is_a_setup_error(store) -> None:
    with pytest.raises(SetupError, match="ingest"):
        store.search("cafes", 5)


def test_search_finds_the_closest_chunk_with_its_source(store) -> None:
    store.sync(
        [
            chunk("a#pasta", "great pasta trattoria"),
            chunk("a#view", "sunset view garden"),
        ]
    )

    hits = store.search("where was the pasta great", 2)

    assert hits[0].id == "a#pasta"
    assert hits[0].source == "a#pasta.md"
    assert hits[0].score > hits[1].score


def test_city_filter_only_returns_that_city(store) -> None:
    store.sync(
        [
            chunk("r#cafe", "lovely cafe", "Rome"),
            chunk("v#cafe", "lovely cafe", "Vienna"),
        ]
    )

    hits = store.search("cafe", 5, city="Vienna")

    assert [h.id for h in hits] == ["v#cafe"]


def test_rerun_with_same_chunks_changes_nothing(store) -> None:
    chunks = [chunk("a#1", "one"), chunk("a#2", "two")]
    store.sync(chunks)

    assert store.sync(chunks) == 0
    assert store.count() == 2


def test_renamed_section_leaves_no_orphan(store) -> None:
    store.sync([chunk("m#cafe", "cafe"), chunk("m#beach", "beach")])

    deleted = store.sync(
        [chunk("m#cafe", "cafe"), chunk("m#sandy-beach", "sandy beach")]
    )

    assert deleted == 1
    assert store.count() == 2
    assert {h.id for h in store.search("beach cafe", 5)} == {"m#cafe", "m#sandy-beach"}


def test_empty_chunks_refuse_to_wipe_the_store(store) -> None:
    store.sync([chunk("a#1", "one")])

    with pytest.raises(ValueError, match="No chunks"):
        store.sync([])

    assert store.count() == 1


def test_sample_notes_round_trip(store) -> None:
    store.sync(load_chunks(SAMPLE_NOTES))

    hits = store.search("microwaved frozen paella", 3, city="Barcelona")

    assert hits[0].id == "barcelona-2022#paella-on-la-rambla"
    assert hits[0].country == "Spain"


def test_folder_mode_persists_and_can_be_reopened(tmp_path: Path, embedder) -> None:
    QdrantMemory(tmp_path / "qdrant", embedder).sync([chunk("a#1", "kept on disk")])

    reopened = QdrantMemory(tmp_path / "qdrant", embedder)

    assert reopened.count() == 1
