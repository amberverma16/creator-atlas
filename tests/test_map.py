"""Tests for UMAP map coordinate generation."""

import numpy as np

from utils.map import run_umap


def test_run_umap_returns_two_dimensions() -> None:
    rng = np.random.default_rng(42)
    matrix = rng.normal(size=(10, 8)).astype(np.float32)
    coords = run_umap(matrix, n_neighbors=5, random_state=42)
    assert coords.shape == (10, 2)
