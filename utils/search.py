"""Semantic search and neighbor lookup over creator embeddings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from utils.config import EMBEDDING_MODEL, NEIGHBOR_COUNT
from utils.embeddings import embeddings_to_matrix

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

RESULT_COLUMNS = ["username", "display_name", "category", "similarity"]


def rank_by_vector(
    query_vector: np.ndarray,
    matrix: np.ndarray,
    *,
    k: int = NEIGHBOR_COUNT,
    exclude_index: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return top-k indices and cosine similarity scores for a query vector."""
    query = np.asarray(query_vector, dtype=np.float32).reshape(-1)
    scores = matrix @ query

    if exclude_index is not None:
        scores = scores.copy()
        scores[exclude_index] = -np.inf

    k = min(k, len(scores))
    top_indices = np.argpartition(scores, -k)[-k:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
    return top_indices, scores[top_indices]


def _results_frame(
    embeddings_df: pd.DataFrame,
    indices: np.ndarray,
    scores: np.ndarray,
) -> pd.DataFrame:
    result = embeddings_df.iloc[indices].copy()
    result["similarity"] = scores
    return result[RESULT_COLUMNS].reset_index(drop=True)


def find_neighbors(
    username: str,
    embeddings_df: pd.DataFrame,
    *,
    k: int = NEIGHBOR_COUNT,
) -> pd.DataFrame:
    """Return the top-k creators most similar to the given username."""
    if embeddings_df.empty or not username:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    usernames = embeddings_df["username"].tolist()
    try:
        index = usernames.index(username)
    except ValueError:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    matrix = embeddings_to_matrix(embeddings_df)
    indices, scores = rank_by_vector(matrix[index], matrix, k=k, exclude_index=index)
    return _results_frame(embeddings_df, indices, scores)


def semantic_search(
    query: str,
    embeddings_df: pd.DataFrame,
    *,
    model: SentenceTransformer | None = None,
    model_name: str = EMBEDDING_MODEL,
    k: int = NEIGHBOR_COUNT,
) -> pd.DataFrame:
    """Return creators whose embeddings best match a natural-language query."""
    if embeddings_df.empty or not query.strip():
        return pd.DataFrame(columns=RESULT_COLUMNS)

    if model is None:
        from utils.embeddings import load_embedding_model

        model = load_embedding_model(model_name)

    query_vector = model.encode(
        [query.strip()],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0]
    matrix = embeddings_to_matrix(embeddings_df)
    indices, scores = rank_by_vector(query_vector, matrix, k=k)
    return _results_frame(embeddings_df, indices, scores)


def format_similarity(score: float) -> str:
    """Format cosine similarity as a readable percentage."""
    return f"{max(0.0, float(score)) * 100:.0f}%"
