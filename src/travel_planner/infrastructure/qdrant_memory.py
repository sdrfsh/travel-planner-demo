"""MemorySearch on Qdrant (local mode): note chunks stored as vectors, searched by meaning.

Local mode keeps everything in a folder (data/qdrant) with no server. That folder
can be open in only one process at a time, so every operation opens the client,
does its work and closes it again: the MCP server and the ingest script can then
take turns. With path=None everything lives in memory (used by the tests).
"""

import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Protocol

from qdrant_client import QdrantClient, models

from travel_planner.application.entities import MemoryHit
from travel_planner.application.errors import SetupError

COLLECTION = "travel_memory"


class Embedder(Protocol):
    dimension: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def point_id(chunk_id: str) -> str:
    """Qdrant ids must be ints or UUIDs: derive a stable UUID from the chunk id."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


class QdrantMemory:
    def __init__(self, path: Path | None, embedder: Embedder) -> None:
        self.path = path
        self.embedder = embedder
        self._in_memory = QdrantClient(":memory:") if path is None else None

    def sync(self, chunks: list[dict[str, Any]]) -> int:
        """Make Qdrant match `chunks` exactly, keyed by chunk id.

        Existing chunks are overwritten, so re-running is safe; chunks that are no
        longer produced (deleted notes, renamed sections) are removed.
        Returns the number of orphans deleted. Raises ValueError on an empty list,
        which would otherwise delete every stored chunk.
        """
        if not chunks:
            raise ValueError("No chunks to sync: refusing to empty the travel memory.")
        vectors = self.embedder.embed([chunk["text"] for chunk in chunks])
        points = [
            models.PointStruct(
                id=point_id(chunk["id"]),
                vector=vector,
                payload={
                    **chunk["metadata"],
                    "chunk_id": chunk["id"],
                    "text": chunk["text"],
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        with self._client() as client:
            if not client.collection_exists(COLLECTION):
                client.create_collection(
                    COLLECTION,
                    vectors_config=models.VectorParams(
                        size=self.embedder.dimension, distance=models.Distance.COSINE
                    ),
                )
            orphans = sorted(_all_ids(client) - {p.id for p in points})
            if orphans:
                client.delete(
                    COLLECTION, points_selector=models.PointIdsList(points=orphans)
                )
            client.upsert(COLLECTION, points=points)
        return len(orphans)

    def search(
        self, query: str, top_k: int, city: str | None = None
    ) -> list[MemoryHit]:
        if self.count() == 0:
            raise SetupError(
                "The travel memory is empty: no trip notes have been ingested yet, "
                "so there is nothing to search. Do not retry this tool and do not "
                "guess an answer. Tell the user to run the ingest script "
                "(`uv run python -m travel_planner.infrastructure.ingest`), then ask again."
            )
        query_filter = None
        if city:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="city", match=models.MatchValue(value=city)
                    )
                ]
            )
        [vector] = self.embedder.embed([query])
        with self._client() as client:
            result = client.query_points(
                COLLECTION,
                query=vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
        return [_to_hit(point.payload or {}, point.score) for point in result.points]

    def count(self) -> int:
        with self._client() as client:
            if not client.collection_exists(COLLECTION):
                return 0
            return client.count(COLLECTION).count

    @contextmanager
    def _client(self) -> Iterator[QdrantClient]:
        if self._in_memory is not None:
            yield self._in_memory
            return
        client = QdrantClient(path=str(self.path))
        try:
            yield client
        finally:
            client.close()


def _all_ids(client: QdrantClient) -> set[str]:
    """Every point id in the collection (scrolls page by page)."""
    ids: set[str] = set()
    offset = None
    while True:
        points, offset = client.scroll(
            COLLECTION, limit=256, offset=offset, with_payload=False, with_vectors=False
        )
        ids.update(str(p.id) for p in points)
        if offset is None:
            return ids


def _to_hit(payload: dict[str, Any], score: float) -> MemoryHit:
    return MemoryHit(
        id=payload.get("chunk_id", ""),
        text=payload.get("text", ""),
        source=payload.get("source"),
        section=payload.get("section"),
        city=payload.get("city"),
        country=payload.get("country"),
        score=round(score, 3),
    )
