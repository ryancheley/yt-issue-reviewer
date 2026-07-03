"""Cosine-similarity helper properties."""

from __future__ import annotations

import numpy as np

from yt_issue_reviewer.embeddings.ollama import cosine_matrix


def test_cosine_symmetric_with_unit_diagonal() -> None:
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    sim = cosine_matrix(vectors)
    assert sim.shape == (3, 3)
    assert np.allclose(np.diag(sim), 1.0)
    assert np.allclose(sim, sim.T)


def test_cosine_known_values() -> None:
    vectors = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    sim = cosine_matrix(vectors)
    assert sim[0, 1] == 1.0  # identical direction
    assert abs(sim[0, 2]) < 1e-9  # orthogonal


def test_cosine_handles_zero_vector() -> None:
    sim = cosine_matrix(np.array([[0.0, 0.0], [1.0, 0.0]]))
    assert not np.isnan(sim).any()
