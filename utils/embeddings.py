"""Embedding generation for creator profiles."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from utils.config import EMBEDDING_MODEL
from utils.data_loader import _load_creators_df
from utils.paths import CREATORS_CSV, EMBEDDINGS_PARQUET
from utils.text import build_embedding_text

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


def load_embeddings_parquet(path: Path = EMBEDDINGS_PARQUET) -> pd.DataFrame:
    """Load precomputed creator embeddings from parquet."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Embeddings not found at {path}. Run `python scripts/build_embeddings.py` first."
        )
    return pd.read_parquet(path)


def add_embedding_text(df: pd.DataFrame) -> pd.DataFrame:
    """Add an embedding_text column built from profile fields."""
    result = df.copy()
    result["embedding_text"] = result.apply(
        lambda row: build_embedding_text(
            display_name=str(row["display_name"]),
            username=str(row["username"]),
            category=str(row["category"]),
            bio=str(row.get("bio") or ""),
            captions=row.get("recent_captions_list") or [],
            hashtags=row.get("hashtags_list") or [],
        ),
        axis=1,
    )
    return result


def load_embedding_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def encode_creators(
    df: pd.DataFrame,
    model: SentenceTransformer | None = None,
    *,
    model_name: str = EMBEDDING_MODEL,
) -> pd.DataFrame:
    """Return a dataframe with creator_id, embedding_text, and embedding vectors."""
    if model is None:
        model = load_embedding_model(model_name)

    texts = df["embedding_text"].tolist()
    vectors = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    output = df[["creator_id", "username", "display_name", "category", "embedding_text"]].copy()
    output["embedding"] = [vector.tolist() for vector in vectors]
    output["embedding_model"] = model_name
    output["embedding_dim"] = int(vectors.shape[1])
    return output


def build_embeddings_from_csv(csv_path=CREATORS_CSV, model_name: str = EMBEDDING_MODEL) -> pd.DataFrame:
    """Load creators, build text blobs, and encode embeddings."""
    creators = _load_creators_df(csv_path)
    if creators.empty:
        raise ValueError(f"No creators found in {csv_path}")

    with_text = add_embedding_text(creators)
    return encode_creators(with_text, model_name=model_name)


def embeddings_to_matrix(df: pd.DataFrame) -> np.ndarray:
    """Stack embedding lists into a 2D numpy array."""
    return np.asarray(df["embedding"].tolist(), dtype=np.float32)
