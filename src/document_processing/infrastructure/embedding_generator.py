"""Local embedding generator adapter using numpy.

This is a development-only adapter that generates random embeddings.
Replace with sentence-transformers or another model for production use.
"""

import numpy as np

from src.study_documents.domain.entities import EMBEDDING_DIMENSION


class NumpyEmbeddingGenerator:
    """Generates embeddings using numpy (development-only, deterministic stub).

    This adapter produces a deterministic embedding based on the input text's
    hash, ensuring the same text always produces the same embedding.
    Replace with sentence-transformers or another model in production.
    """

    def __init__(self, dimension: int = EMBEDDING_DIMENSION) -> None:
        self._dimension = dimension
        self._rng = np.random.default_rng(42)

    async def generate(self, text: str) -> list[float]:
        """Generate a deterministic embedding for the given text."""
        seed = hash(text) & 0xFFFFFFFF
        rng = np.random.default_rng(seed)
        vector = rng.uniform(-0.1, 0.1, size=self._dimension)
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()
