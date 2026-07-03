"""Embedding generation behind an interface (self-hosted Ollama only).

Includes a pure cosine-similarity helper and a deterministic fake for tests. No path here
ever contacts a third-party hosted service (Constitution I).
"""

from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np

from ..errors import OllamaUnavailable

# Task prefixes required by certain embedding models on the document/corpus side.
_DOC_PREFIXES: dict[str, str] = {
    "nomic-embed-text": "search_document: ",
}


def document_prefix(model: str) -> str:
    """Return the corpus-side task prefix for a model (empty if none required)."""
    base = model.split(":", 1)[0]
    return _DOC_PREFIXES.get(base, "")


def cosine_matrix(vectors: np.ndarray) -> np.ndarray:
    """NxN cosine-similarity matrix for the given row vectors. Pure, no I/O."""
    if vectors.ndim != 2:
        raise ValueError("expected a 2-D array of row vectors")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized = vectors / norms
    sim = normalized @ normalized.T
    return np.clip(sim, -1.0, 1.0)


class Embedder(Protocol):
    model: str
    model_version: str | None
    dim: int

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

    def check_available(self) -> None: ...


class FakeEmbedder:
    """Deterministic bag-of-words embedder so known-related fixtures are similar."""

    def __init__(self, model: str = "fake-embed", dim: int = 64, *, available: bool = True) -> None:
        self.model = model
        self.model_version: str | None = "fake-1"
        self.dim = dim
        self._available = available

    def check_available(self) -> None:
        if not self._available:
            raise OllamaUnavailable("fake embedder configured as unavailable")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.check_available()
        return [self._vector(t) for t in texts]

    def _vector(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float64)
        for token in _tokenize(text):
            idx = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[idx] += 1.0
        return vec.tolist()


class OllamaEmbedder:
    """Production embedder using the official ``ollama`` client and ``/api/embed``."""

    def __init__(self, host: str, model: str, *, batch_size: int = 64) -> None:
        from ollama import Client

        self._client = Client(host=host)
        self.model = model
        self.model_version: str | None = None
        self.dim = 0
        self._batch_size = batch_size
        self._prefix = document_prefix(model)

    def check_available(self) -> None:
        try:
            listing = self._client.list()
        except Exception as exc:  # noqa: BLE001 - surface any connectivity failure uniformly
            raise OllamaUnavailable(
                f"cannot reach Ollama: {exc}. Check --ollama-host / OLLAMA_HOST."
            ) from exc
        names = {m.get("model") or m.get("name") for m in getattr(listing, "models", [])}
        base = self.model.split(":", 1)[0]
        if not any(n and n.split(":", 1)[0] == base for n in names):
            raise OllamaUnavailable(
                f"embedding model '{self.model}' is not pulled. Run `ollama pull {self.model}`."
            )

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        prefixed = [self._prefix + t for t in texts]
        vectors: list[list[float]] = []
        for start in range(0, len(prefixed), self._batch_size):
            chunk = prefixed[start : start + self._batch_size]
            try:
                resp = self._client.embed(model=self.model, input=chunk)
            except Exception as exc:  # noqa: BLE001
                raise OllamaUnavailable(f"embedding request failed: {exc}") from exc
            batch = [list(map(float, v)) for v in resp["embeddings"]]
            vectors.extend(batch)
        if vectors:
            self.dim = len(vectors[0])
        return vectors


def _tokenize(text: str) -> list[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]
