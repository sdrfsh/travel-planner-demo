"""Text -> vectors with FastEmbed: a small local model, no API key, no PyTorch."""

from collections.abc import Sequence

from fastembed import TextEmbedding

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


class FastEmbedEmbedder:
    """Embeds texts locally. The model (~70 MB) downloads once on first use."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self.dimension = TextEmbedding.get_embedding_size(model_name)
        self._model: TextEmbedding | None = (
            None  # loaded lazily: the server starts fast
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self._model is None:
            self._model = TextEmbedding(self.model_name)
        return [vector.tolist() for vector in self._model.embed(list(texts))]
