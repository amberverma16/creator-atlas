"""UMAP dimensionality reduction for creator map coordinates."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from utils.config import (
    UMAP_METRIC,
    UMAP_MIN_DIST,
    UMAP_N_NEIGHBORS,
    UMAP_RANDOM_STATE,
)
from utils.embeddings import embeddings_to_matrix, load_embeddings_parquet
from utils.paths import CREATORS_CSV, EMBEDDINGS_PARQUET, MAP_COORDS_PARQUET


def run_umap(
    matrix: np.ndarray,
    *,
    n_neighbors: int = UMAP_N_NEIGHBORS,
    min_dist: float = UMAP_MIN_DIST,
    metric: str = UMAP_METRIC,
    random_state: int = UMAP_RANDOM_STATE,
) -> np.ndarray:
    """Reduce embedding matrix to 2D coordinates."""
    import umap

    n_samples = matrix.shape[0]
    if n_samples < 2:
        raise ValueError("Need at least 2 creators to run UMAP.")

    effective_neighbors = min(n_neighbors, n_samples - 1)

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=effective_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=random_state,
    )
    return reducer.fit_transform(matrix)


def build_map_coords(
    embeddings_path: Path = EMBEDDINGS_PARQUET,
    creators_path: Path = CREATORS_CSV,
    *,
    n_neighbors: int = UMAP_N_NEIGHBORS,
    min_dist: float = UMAP_MIN_DIST,
    metric: str = UMAP_METRIC,
    random_state: int = UMAP_RANDOM_STATE,
) -> pd.DataFrame:
    """Load embeddings, run UMAP, and return map-ready creator coordinates."""
    embeddings_df = load_embeddings_parquet(embeddings_path)
    matrix = embeddings_to_matrix(embeddings_df)
    coords = run_umap(
        matrix,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=random_state,
    )

    map_df = embeddings_df[["creator_id", "username", "display_name", "category"]].copy()
    map_df["x"] = coords[:, 0]
    map_df["y"] = coords[:, 1]

    from utils.data_loader import _load_creators_df

    creators = _load_creators_df(creators_path)
    enrich_cols = ["creator_id", "bio", "followers", "avg_likes", "avg_views", "profile_url"]
    available = [col for col in enrich_cols if col in creators.columns]
    map_df = map_df.merge(creators[available], on="creator_id", how="left")

    return map_df


def load_map_coords(path: Path = MAP_COORDS_PARQUET) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Map coordinates not found at {path}. Run `python scripts/build_map.py` first."
        )
    return pd.read_parquet(path)
