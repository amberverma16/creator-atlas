"""Tests for embedding text and pipeline helpers."""

import pandas as pd

from utils.embeddings import add_embedding_text, embeddings_to_matrix
from utils.text import build_embedding_text


def test_build_embedding_text_includes_profile_fields() -> None:
    text = build_embedding_text(
        display_name="Test Creator",
        username="testcreator",
        category="Comedy",
        bio="Making people laugh.",
        captions=["joke one", "joke two"],
        hashtags=["comedy", "funny"],
    )
    assert "Test Creator" in text
    assert "@testcreator" in text
    assert "Comedy" in text
    assert "Making people laugh." in text
    assert "joke one" in text
    assert "comedy" in text


def test_add_embedding_text_column() -> None:
    df = pd.DataFrame(
        [
            {
                "creator_id": "testcreator",
                "username": "testcreator",
                "display_name": "Test Creator",
                "category": "Comedy",
                "bio": "Making people laugh.",
                "recent_captions_list": ["joke one"],
                "hashtags_list": ["comedy"],
            }
        ]
    )
    result = add_embedding_text(df)
    assert "embedding_text" in result.columns
    assert "Test Creator" in result.iloc[0]["embedding_text"]


def test_embeddings_to_matrix_shape() -> None:
    df = pd.DataFrame({"embedding": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]})
    matrix = embeddings_to_matrix(df)
    assert matrix.shape == (2, 3)
