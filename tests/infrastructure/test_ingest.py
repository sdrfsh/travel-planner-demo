"""Tests for ingest: turning Markdown notes into chunks."""

from pathlib import Path

import pytest

from travel_planner.infrastructure.ingest import load_chunks

NOTE = """\
---
trip: Porto 2024
city: Porto
country: Portugal
start_date: 2024-04-10
---
# Porto

## Serra do Pilar
type: viewpoint
verdict: loved

## Overall
Great food, slow buses.
"""


def write_note(folder: Path, name: str, text: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    # utf-8-sig writes a BOM, like Windows editors do
    (folder / name).write_text(text, encoding="utf-8-sig")


def test_one_chunk_per_section_with_stable_ids(tmp_path: Path) -> None:
    write_note(tmp_path, "porto.md", NOTE)

    chunks = load_chunks(tmp_path)

    assert [c["id"] for c in chunks] == [
        "porto#serra-do-pilar",
        "porto#overall",
    ]


def test_chunk_text_has_heading_and_country(tmp_path: Path) -> None:
    write_note(tmp_path, "porto.md", NOTE)

    first = load_chunks(tmp_path)[0]

    assert first["text"].startswith("Serra do Pilar\nCountry: Portugal")
    assert first["metadata"]["source"] == "porto.md"
    assert first["metadata"]["start_date"] == "2024-04-10"  # YAML date -> text


def test_repeated_heading_gets_a_unique_id(tmp_path: Path) -> None:
    write_note(tmp_path, "x.md", "## Cafe\none\n## Cafe\ntwo\n")

    assert [c["id"] for c in load_chunks(tmp_path)] == ["x#cafe", "x#cafe-2"]


def test_missing_or_empty_notes_folder_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_chunks(tmp_path / "nope")
    with pytest.raises(FileNotFoundError):
        load_chunks(tmp_path)  # exists, but has no .md files
