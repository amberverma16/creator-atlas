"""Tests for Plotly map visualization."""

import pandas as pd

from utils.viz import (
    LOD_TIER_DOTS,
    LOD_TIER_LABELS,
    LOD_TIER_REGIONS,
    _filter_non_overlapping,
    build_creator_map_figure,
    compute_map_bounds,
    infer_lod_tier,
)


def _sample_df(n: int = 6) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append(
            {
                "username": f"user{i}",
                "display_name": f"User {i}",
                "category": "Comedy" if i % 2 == 0 else "Dance",
                "x": float(i),
                "y": float(i) * 1.5,
                "followers": (n - i) * 10_000,
            }
        )
    return pd.DataFrame(rows)


def test_default_view_shows_regions_only() -> None:
    df = _sample_df(4)
    bounds = compute_map_bounds(df)
    fig, trace_frames, clickable_curves, tier = build_creator_map_figure(
        df,
        lod_tier=LOD_TIER_REGIONS,
        bounds=bounds,
    )
    assert tier == LOD_TIER_REGIONS
    assert len(trace_frames) == 0
    assert len(clickable_curves) == 0
    assert len(fig.data) >= 2


def test_dots_tier_exposes_clickable_traces() -> None:
    df = _sample_df(4)
    bounds = compute_map_bounds(df)
    fig, trace_frames, clickable_curves, tier = build_creator_map_figure(
        df,
        lod_tier=LOD_TIER_DOTS,
        bounds=bounds,
    )
    assert tier == LOD_TIER_DOTS
    assert len(trace_frames) == 2
    assert len(clickable_curves) == 2
    assert len(fig.data) >= 4


def test_labels_tier_includes_name_traces() -> None:
    df = _sample_df(4)
    bounds = compute_map_bounds(df)
    fig, trace_frames, _, tier = build_creator_map_figure(
        df,
        lod_tier=LOD_TIER_LABELS,
        selected_username="user0",
        bounds=bounds,
    )
    assert tier == LOD_TIER_LABELS
    text_traces = [t for t in fig.data if getattr(t, "mode", "") == "text"]
    assert text_traces


def test_infer_lod_tier_thresholds() -> None:
    assert infer_lod_tier(1.0) == LOD_TIER_REGIONS
    assert infer_lod_tier(2.0) == LOD_TIER_DOTS
    assert infer_lod_tier(4.0) == LOD_TIER_LABELS


def test_filter_non_overlapping_keeps_higher_priority() -> None:
    items = [(0.0, 0.0, 1.0), (0.05, 0.0, 10.0), (5.0, 5.0, 5.0)]
    kept = _filter_non_overlapping(items, min_sep=0.2)
    assert 1 in kept
    assert 2 in kept
    assert 0 not in kept
