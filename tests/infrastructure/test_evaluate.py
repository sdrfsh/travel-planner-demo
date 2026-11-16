"""Tests for the retrieval evaluation."""

from pathlib import Path

import pytest

from travel_planner.infrastructure.evaluate import hit_rate_at_k, load_eval_set, run
from travel_planner.infrastructure.ingest import load_chunks
from travel_planner.infrastructure.qdrant_memory import QdrantMemory

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "data"


def test_hit_rate_counts_expected_in_retrieved() -> None:
    retrieved = [["a", "b"], ["c"], ["d", "e"]]

    assert hit_rate_at_k(retrieved, ["b", "x", "d"]) == pytest.approx(2 / 3)


def test_empty_eval_set_is_an_error() -> None:
    with pytest.raises(ValueError, match="empty"):
        hit_rate_at_k([], [])


def test_sample_eval_set_points_at_real_chunks() -> None:
    chunk_ids = {c["id"] for c in load_chunks(EXAMPLES / "notes")}

    cases = load_eval_set(EXAMPLES / "eval.yaml")

    assert len(cases) >= 15
    assert {c["expected"] for c in cases} <= chunk_ids


def test_run_end_to_end_with_fake_embedder(embedder, capsys) -> None:
    memory = QdrantMemory(None, embedder)
    memory.sync(load_chunks(EXAMPLES / "notes"))

    rate = run(memory, load_eval_set(EXAMPLES / "eval.yaml"))

    assert 0 < rate <= 1
    assert "hit rate@5" in capsys.readouterr().out
