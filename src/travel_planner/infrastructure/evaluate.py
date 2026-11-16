"""Retrieval evaluation: does the expected note come back in the top k?

Run: `uv run python -m travel_planner.infrastructure.evaluate`
Reads the eval set (data/eval.yaml): a list of {question, expected, city?},
where `expected` is a chunk id like "rome-2025#trattoria-da-lucia".
"""

from pathlib import Path

import yaml

from travel_planner.application.ports import MemorySearch

K = 5


def hit_rate_at_k(retrieved: list[list[str]], expected: list[str]) -> float:
    """Share of questions whose expected chunk id is among the retrieved ids."""
    if not expected:
        raise ValueError("The eval set is empty.")
    hits = sum(exp in ids for ids, exp in zip(retrieved, expected, strict=True))
    return hits / len(expected)


def load_eval_set(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or []


def run(memory: MemorySearch, cases: list[dict], k: int = K) -> float:
    """Search every question, print hit/miss per question, return hit rate@k."""
    retrieved = []
    for case in cases:
        ids = [
            hit.id for hit in memory.search(case["question"], k, city=case.get("city"))
        ]
        retrieved.append(ids)
        mark = "HIT " if case["expected"] in ids else "MISS"
        print(f"{mark} {case['question']}  ->  {ids[:3]}")
    rate = hit_rate_at_k(retrieved, [case["expected"] for case in cases])
    print(f"\nhit rate@{k}: {rate:.0%} ({len(cases)} questions)")
    return rate


if __name__ == "__main__":
    from travel_planner.infrastructure.config import get_settings
    from travel_planner.infrastructure.embeddings import FastEmbedEmbedder
    from travel_planner.infrastructure.qdrant_memory import QdrantMemory

    settings = get_settings()
    run(
        QdrantMemory(settings.qdrant_path, FastEmbedEmbedder()),
        load_eval_set(settings.eval_path),
    )
