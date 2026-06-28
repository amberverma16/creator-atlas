"""Plotly visualization helpers for Creator Atlas."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.config import MAP_HEIGHT


def _marker_sizes(followers: pd.Series) -> list[float]:
    """Map follower counts to readable marker sizes."""
    filled = followers.fillna(0).clip(lower=1)
    sizes = filled.map(lambda v: 8 + (float(v) ** 0.35) / 8)
    return sizes.clip(upper=28).tolist()


def _category_color_map(categories: list[str]) -> dict[str, str]:
    palette = px.colors.qualitative.Dark24
    return {category: palette[index % len(palette)] for index, category in enumerate(sorted(categories))}


def build_creator_map_figure(
    df: pd.DataFrame,
    *,
    selected_username: str | None = None,
    height: int = MAP_HEIGHT,
) -> tuple[go.Figure, list[pd.DataFrame]]:
    """
    Build an interactive scatter plot of creator map coordinates.

    Returns the figure plus trace dataframes (one per category) for selection handling.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=height,
            title="No creators to display",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#E6EDF3"},
        )
        return fig, []

    plot_df = df.copy()
    color_map = _category_color_map(plot_df["category"].dropna().unique().tolist())
    trace_frames: list[pd.DataFrame] = []

    fig = go.Figure()

    for category in sorted(plot_df["category"].dropna().unique()):
        subset = plot_df[plot_df["category"] == category].copy()
        trace_frames.append(subset)

        selected_mask = (
            subset["username"] == selected_username if selected_username else pd.Series(False, index=subset.index)
        )
        base_sizes = _marker_sizes(subset["followers"])
        highlight_sizes = [
            size + 10 if is_selected else size for size, is_selected in zip(base_sizes, selected_mask, strict=True)
        ]

        fig.add_trace(
            go.Scatter(
                x=subset["x"],
                y=subset["y"],
                mode="markers",
                name=str(category),
                marker=dict(
                    size=highlight_sizes,
                    color=color_map[str(category)],
                    opacity=0.9,
                    line=dict(
                        width=[3 if sel else 0 for sel in selected_mask],
                        color="#FFFFFF",
                    ),
                ),
                customdata=subset["username"],
                text=subset["display_name"],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "@%{customdata}<br>"
                    "Category: "
                    + str(category)
                    + "<br>"
                    "Followers: %{meta}<br>"
                    "<extra></extra>"
                ),
                meta=subset["followers"].fillna(0).map(lambda v: f"{int(v):,}" if v else "—"),
            )
        )

    fig.update_layout(
        height=height,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        title="Creator landscape",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#E6EDF3"},
        legend={"title": "Category", "orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        xaxis={
            "title": "",
            "showgrid": True,
            "gridcolor": "rgba(48, 54, 61, 0.6)",
            "zeroline": False,
            "showticklabels": False,
        },
        yaxis={
            "title": "",
            "showgrid": True,
            "gridcolor": "rgba(48, 54, 61, 0.6)",
            "zeroline": False,
            "showticklabels": False,
        },
        hovermode="closest",
    )

    return fig, trace_frames


def username_from_map_selection(event, trace_frames: list[pd.DataFrame]) -> str | None:
    """Extract username from a Streamlit Plotly selection event."""
    if event is None or not getattr(event, "selection", None):
        return None

    points = event.selection.get("points", []) if isinstance(event.selection, dict) else event.selection.points
    if not points:
        return None

    point = points[0]
    curve_number = point.get("curve_number", point.get("curveNumber"))
    point_index = point.get("point_index", point.get("pointIndex"))

    if curve_number is None or point_index is None:
        return None

    try:
        return str(trace_frames[int(curve_number)].iloc[int(point_index)]["username"])
    except (IndexError, ValueError, KeyError):
        return None
