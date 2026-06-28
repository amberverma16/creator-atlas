"""Tests for Plotly map visualization."""

import pandas as pd

from utils.viz import build_creator_map_figure


def test_build_creator_map_figure_returns_traces() -> None:
    df = pd.DataFrame(
        [
            {"username": "a", "display_name": "A", "category": "Comedy", "x": 1.0, "y": 2.0, "followers": 10000},
            {"username": "b", "display_name": "B", "category": "Dance", "x": 3.0, "y": 4.0, "followers": 20000},
        ]
    )
    fig, trace_frames = build_creator_map_figure(df, selected_username="a")
    assert len(fig.data) == 2
    assert len(trace_frames) == 2
