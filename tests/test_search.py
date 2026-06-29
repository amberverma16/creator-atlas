"""Tests for semantic search and neighbor lookup."""

import numpy as np
import pandas as pd

from utils.search import find_neighbors, format_similarity, rank_by_vector, semantic_search


def _sample_embeddings_df() -> pd.DataFrame:
    vectors = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    return pd.DataFrame(
        {
            "username": ["alpha", "beta", "gamma", "delta"],
            "display_name": ["Alpha", "Beta", "Gamma", "Delta"],
            "category": ["A", "A", "B", "C"],
            "embedding": [vector.tolist() for vector in vectors],
        }
    )


def test_rank_by_vector_excludes_self() -> None:
    matrix = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    indices, scores = rank_by_vector(matrix[0], matrix, k=1, exclude_index=0)
    assert indices.tolist() == [1]
    assert scores.tolist() == [0.0]


def test_find_neighbors_excludes_selected_creator() -> None:
    df = _sample_embeddings_df()
    neighbors = find_neighbors("alpha", df, k=2)
    assert list(neighbors["username"]) == ["beta", "delta"]
    assert "alpha" not in neighbors["username"].values


def test_semantic_search_ranks_closest_vector() -> None:
    df = _sample_embeddings_df()

    class FakeModel:
        def encode(self, texts, *, normalize_embeddings, convert_to_numpy):
            assert texts == ["dance creator"]
            return np.array([[0.0, 1.0, 0.0]], dtype=np.float32)

    matches = semantic_search("dance creator", df, model=FakeModel(), k=2)
    assert list(matches["username"]) == ["gamma", "beta"]


def test_format_similarity() -> None:
    assert format_similarity(0.876) == "88%"
