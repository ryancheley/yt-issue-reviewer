"""Contract tests for the Embedder interface via FakeEmbedder."""

from __future__ import annotations

import numpy as np
import pytest

from yt_issue_reviewer.embeddings.ollama import FakeEmbedder, cosine_matrix
from yt_issue_reviewer.errors import OllamaUnavailable


def test_embed_batch_one_vector_per_input() -> None:
    emb = FakeEmbedder(dim=32)
    texts = ["login error 500", "csv export empty", "dark mode"]
    vectors = emb.embed_batch(texts)
    assert len(vectors) == len(texts)
    assert all(len(v) == 32 for v in vectors)


def test_related_texts_are_more_similar_than_unrelated() -> None:
    emb = FakeEmbedder(dim=128)
    vectors = np.array(
        emb.embed_batch(
            [
                "login page returns 500 server error on submit",
                "signing in fails with internal server error 500",
                "add dark mode to the settings screen",
            ]
        )
    )
    sim = cosine_matrix(vectors)
    assert sim[0, 1] > sim[0, 2]


def test_unavailable_embedder_raises() -> None:
    with pytest.raises(OllamaUnavailable):
        FakeEmbedder(available=False).embed_batch(["x"])
