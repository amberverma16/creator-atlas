"""Prepare map data and render the interactive atlas component."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components

GALAXY_PALETTE = [
    "#b794f6", "#9f7aea", "#805ad5", "#6b46c1",
    "#4fd1c5", "#f687b3", "#f6ad55", "#63b3ed", "#fc8181", "#d6bcfa",
]

_COMPONENT_PATH = Path(__file__).resolve().parent.parent / "components" / "atlas_map" / "frontend"
atlas_map = components.declare_component("atlas_map", path=str(_COMPONENT_PATH))


def _category_colors(categories: list[str]) -> dict[str, str]:
    sorted_cats = sorted(categories)
    return {cat: GALAXY_PALETTE[i % len(GALAXY_PALETTE)] for i, cat in enumerate(sorted_cats)}


def prepare_map_payload(df: pd.DataFrame) -> dict:
    """Serialize creator coordinates for the client-side LOD map."""
    if df.empty:
        return {"creators": [], "categories": [], "bounds": {"x": [0, 1], "y": [0, 1]}}

    plot_df = df.copy()
    colors = _category_colors(plot_df["category"].dropna().unique().tolist())

    categories = []
    for category, group in plot_df.groupby("category"):
        categories.append(
            {
                "name": str(category),
                "x": float(group["x"].mean()),
                "y": float(group["y"].mean()),
                "count": int(len(group)),
                "color": colors[str(category)],
            }
        )

    creators = []
    for row in plot_df.itertuples(index=False):
        creators.append(
            {
                "username": str(row.username),
                "display_name": str(row.display_name),
                "category": str(row.category),
                "x": float(row.x),
                "y": float(row.y),
                "followers": int(row.followers) if pd.notna(row.followers) else 0,
                "color": colors.get(str(row.category), "#b794f6"),
            }
        )

    x_pad = (plot_df["x"].max() - plot_df["x"].min()) * 0.15 or 1.0
    y_pad = (plot_df["y"].max() - plot_df["y"].min()) * 0.15 or 1.0

    return {
        "creators": creators,
        "categories": categories,
        "bounds": {
            "x": [float(plot_df["x"].min() - x_pad), float(plot_df["x"].max() + x_pad)],
            "y": [float(plot_df["y"].min() - y_pad), float(plot_df["y"].max() + y_pad)],
        },
    }


def render_atlas_map(
    df: pd.DataFrame,
    *,
    selected_username: str | None = None,
    height: int = 900,
    key: str | None = None,
) -> dict | None:
    """Render the full-viewport LOD map. Returns {username} when a creator is clicked."""
    payload = prepare_map_payload(df)
    result = atlas_map(
        data=json.dumps(payload),
        selected=selected_username or "",
        height=height,
        key=key,
        default=None,
    )
    if isinstance(result, dict):
        return result
    return None
