"""Plotly visualization — Apple Maps-style progressive disclosure atlas."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from utils.config import LOD_DOTS_ZOOM, LOD_LABELS_ZOOM, MAP_HEIGHT, MAX_REGION_LABELS

GALAXY_PALETTE = [
    "#b794f6",
    "#9f7aea",
    "#805ad5",
    "#6b46c1",
    "#4fd1c5",
    "#f687b3",
    "#f6ad55",
    "#63b3ed",
    "#fc8181",
    "#d6bcfa",
]

LOD_TIER_REGIONS = 0
LOD_TIER_DOTS = 1
LOD_TIER_LABELS = 2


def _category_color_map(categories: list[str]) -> dict[str, str]:
    sorted_cats = sorted(categories)
    return {cat: GALAXY_PALETTE[i % len(GALAXY_PALETTE)] for i, cat in enumerate(sorted_cats)}


def compute_map_bounds(df: pd.DataFrame, *, pad_frac: float = 0.12) -> dict[str, list[float]]:
    """Axis bounds with padding for the full atlas view."""
    if df.empty:
        return {"x": [0.0, 1.0], "y": [0.0, 1.0]}

    x_min, x_max = float(df["x"].min()), float(df["x"].max())
    y_min, y_max = float(df["y"].min()), float(df["y"].max())
    x_pad = (x_max - x_min) * pad_frac or 1.0
    y_pad = (y_max - y_min) * pad_frac or 1.0
    return {
        "x": [x_min - x_pad, x_max + x_pad],
        "y": [y_min - y_pad, y_max + y_pad],
    }


def compute_zoom_factor(
    bounds: dict[str, list[float]],
    x_range: tuple[float, float] | None,
    y_range: tuple[float, float] | None,
) -> float:
    """How far zoomed in relative to the full atlas (1 = full view)."""
    if not x_range or not y_range:
        return 1.0

    full_w = bounds["x"][1] - bounds["x"][0]
    full_h = bounds["y"][1] - bounds["y"][0]
    view_w = max(x_range[1] - x_range[0], 1e-9)
    view_h = max(y_range[1] - y_range[0], 1e-9)
    return max(full_w / view_w, full_h / view_h)


def infer_lod_tier(zoom_factor: float) -> int:
    """Map zoom level to disclosure tier."""
    if zoom_factor < LOD_DOTS_ZOOM:
        return LOD_TIER_REGIONS
    if zoom_factor < LOD_LABELS_ZOOM:
        return LOD_TIER_DOTS
    return LOD_TIER_LABELS


def zoom_ranges(
    bounds: dict[str, list[float]],
    *,
    zoom_factor: float,
    center_x: float | None = None,
    center_y: float | None = None,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Visible axis ranges for a given zoom centered on a point."""
    full_w = bounds["x"][1] - bounds["x"][0]
    full_h = bounds["y"][1] - bounds["y"][0]
    cx = center_x if center_x is not None else (bounds["x"][0] + bounds["x"][1]) / 2
    cy = center_y if center_y is not None else (bounds["y"][0] + bounds["y"][1]) / 2

    view_w = full_w / max(zoom_factor, 1.0)
    view_h = full_h / max(zoom_factor, 1.0)
    x_range = (cx - view_w / 2, cx + view_w / 2)
    y_range = (cy - view_h / 2, cy + view_h / 2)
    return x_range, y_range


def _marker_sizes(followers: pd.Series, *, scale: float = 1.0) -> list[float]:
    filled = followers.fillna(0).clip(lower=1)
    sizes = filled.map(lambda v: (5 + (float(v) ** 0.28) / 10) * scale)
    return sizes.clip(lower=4, upper=14).tolist()


def _category_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-category centroid, spread, and count."""
    rows: list[dict[str, Any]] = []
    x_span = float(df["x"].max() - df["x"].min()) or 1.0
    y_span = float(df["y"].max() - df["y"].min()) or 1.0
    min_rx = x_span * 0.06
    min_ry = y_span * 0.06

    for category, group in df.groupby("category"):
        cx = float(group["x"].mean())
        cy = float(group["y"].mean())
        std_x = float(group["x"].std(ddof=0) or 0)
        std_y = float(group["y"].std(ddof=0) or 0)
        rows.append(
            {
                "category": str(category),
                "x": cx,
                "y": cy,
                "rx": max(std_x * 1.8, min_rx),
                "ry": max(std_y * 1.8, min_ry),
                "count": len(group),
            }
        )
    return pd.DataFrame(rows)


def _ellipse_points(cx: float, cy: float, rx: float, ry: float, *, n: int = 56) -> tuple[list[float], list[float]]:
    xs = [cx + rx * math.cos(2 * math.pi * i / n) for i in range(n + 1)]
    ys = [cy + ry * math.sin(2 * math.pi * i / n) for i in range(n + 1)]
    return xs, ys


def _in_viewport(
    x: float,
    y: float,
    x_range: tuple[float, float] | None,
    y_range: tuple[float, float] | None,
    *,
    pad_frac: float = 0.1,
) -> bool:
    if not x_range or not y_range:
        return True
    pad_x = (x_range[1] - x_range[0]) * pad_frac
    pad_y = (y_range[1] - y_range[0]) * pad_frac
    return (
        x_range[0] - pad_x <= x <= x_range[1] + pad_x
        and y_range[0] - pad_y <= y <= y_range[1] + pad_y
    )


def _filter_non_overlapping(
    items: list[tuple[float, float, float]],
    min_sep: float,
) -> list[int]:
    """Keep highest-priority labels that do not overlap (returns kept indices)."""
    order = sorted(range(len(items)), key=lambda i: -items[i][2])
    kept_points: list[tuple[float, float]] = []
    kept_indices: list[int] = []
    min_sep_sq = min_sep * min_sep

    for idx in order:
        x, y, _ = items[idx]
        if all((x - px) ** 2 + (y - py) ** 2 >= min_sep_sq for px, py in kept_points):
            kept_points.append((x, y))
            kept_indices.append(idx)
    return kept_indices


def _add_grid(fig: go.Figure, bounds: dict[str, list[float]]) -> None:
    grid_x = bounds["x"]
    grid_y = bounds["y"]
    for frac in (0.25, 0.5, 0.75):
        gx = grid_x[0] + (grid_x[1] - grid_x[0]) * frac
        gy = grid_y[0] + (grid_y[1] - grid_y[0]) * frac
        fig.add_trace(
            go.Scatter(
                x=[gx, gx],
                y=grid_y,
                mode="lines",
                line=dict(color="rgba(196,181,253,0.05)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=grid_x,
                y=[gy, gy],
                mode="lines",
                line=dict(color="rgba(196,181,253,0.05)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )


def _add_region_tier(
    fig: go.Figure,
    plot_df: pd.DataFrame,
    color_map: dict[str, str],
    *,
    x_range: tuple[float, float] | None,
    y_range: tuple[float, float] | None,
) -> None:
    """Tier 0 — subtle region outlines and a handful of large category labels."""
    stats = _category_stats(plot_df)
    if stats.empty:
        return

    x_span = (x_range[1] - x_range[0]) if x_range else float(plot_df["x"].max() - plot_df["x"].min()) or 1.0
    label_sep = x_span * 0.14

    ranked = stats.sort_values("count", ascending=False)
    label_categories = set(ranked.head(MAX_REGION_LABELS)["category"])
    outline_categories = set(ranked.head(max(MAX_REGION_LABELS, 10))["category"])

    label_candidates: list[tuple[float, float, float, str]] = []
    for _, row in stats.iterrows():
        cat = row["category"]
        if cat not in label_categories:
            continue
        if not _in_viewport(row["x"], row["y"], x_range, y_range):
            continue
        label_candidates.append((row["x"], row["y"], float(row["count"]), cat))

    kept_label_indices = _filter_non_overlapping(
        [(x, y, pri) for x, y, pri, _ in label_candidates],
        label_sep,
    )
    labeled_cats = {label_candidates[i][3] for i in kept_label_indices}

    for _, row in stats.iterrows():
        cat = str(row["category"])
        color = color_map.get(cat, "#c4b5fd")
        cx, cy, rx, ry = row["x"], row["y"], row["rx"], row["ry"]

        if cat not in outline_categories:
            continue

        if not _in_viewport(cx, cy, x_range, y_range):
            continue

        ex, ey = _ellipse_points(cx, cy, rx * 1.15, ry * 1.15)
        fig.add_trace(
            go.Scatter(
                x=ex,
                y=ey,
                mode="lines",
                line=dict(color=color, width=1.2),
                opacity=0.12,
                fill="none",
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ex,
                y=ey,
                mode="lines",
                line=dict(color=color, width=3),
                opacity=0.06,
                fill="none",
                hoverinfo="skip",
                showlegend=False,
            )
        )

        if cat not in labeled_cats:
            continue

        label_y = cy + ry * 0.35
        fig.add_trace(
            go.Scatter(
                x=[cx],
                y=[label_y],
                mode="text",
                text=[cat.upper()],
                textfont=dict(size=20, color=color, family="Inter, sans-serif"),
                textposition="middle center",
                hoverinfo="skip",
                showlegend=False,
                opacity=0.18,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[cx],
                y=[label_y],
                mode="text",
                text=[cat],
                textfont=dict(size=15, color="rgba(245,240,255,0.92)", family="Inter, sans-serif"),
                textposition="middle center",
                hoverinfo="skip",
                showlegend=False,
                opacity=0.88,
            )
        )


def _add_dots_tier(
    fig: go.Figure,
    plot_df: pd.DataFrame,
    color_map: dict[str, str],
    *,
    x_range: tuple[float, float] | None,
    y_range: tuple[float, float] | None,
    selected_username: str | None,
    trace_frames: list[pd.DataFrame],
    clickable_curves: dict[int, int],
    show_names: bool,
) -> None:
    """Tier 1+ — creator dots; names only when show_names is True (tier 2)."""
    has_selection = bool(selected_username)
    view_df = plot_df[
        plot_df.apply(
            lambda r: _in_viewport(float(r["x"]), float(r["y"]), x_range, y_range),
            axis=1,
        )
    ]
    if view_df.empty:
        return

    if show_names and x_range:
        label_offset = (x_range[1] - x_range[0]) * 0.022
        label_sep = label_offset * 1.6
    else:
        label_offset = 0.0
        label_sep = 0.0

    label_rows: list[tuple[float, float, float, pd.Series]] = []
    if show_names and selected_username and selected_username in view_df["username"].values:
        sel_row = view_df[view_df["username"] == selected_username].iloc[0]
        label_rows.append(
            (float(sel_row["x"]) + label_offset, float(sel_row["y"]), 1e6, sel_row)
        )

    for category in sorted(view_df["category"].dropna().unique()):
        subset = view_df[view_df["category"] == category].copy()
        color = color_map[str(category)]
        is_selected = (
            subset["username"] == selected_username
            if selected_username
            else pd.Series(False, index=subset.index)
        )

        fig.add_trace(
            go.Scatter(
                x=subset["x"],
                y=subset["y"],
                mode="markers",
                marker=dict(
                    size=_marker_sizes(subset["followers"], scale=1.8),
                    color=color,
                    opacity=[
                        0.3 if sel else (0.06 if has_selection else 0.14)
                        for sel in is_selected
                    ],
                    line=dict(width=0),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        trace_frames.append(subset)
        clickable_curves[len(fig.data)] = len(trace_frames) - 1
        sizes = _marker_sizes(subset["followers"])
        sizes = [s + 5 if sel else s for s, sel in zip(sizes, is_selected, strict=True)]

        fig.add_trace(
            go.Scatter(
                x=subset["x"],
                y=subset["y"],
                mode="markers",
                name=str(category),
                marker=dict(
                    size=sizes,
                    color=color,
                    opacity=[
                        1.0 if sel else (0.22 if has_selection else 0.88)
                        for sel in is_selected
                    ],
                    line=dict(
                        width=[2 if sel else 0 for sel in is_selected],
                        color="#ffffff",
                    ),
                ),
                customdata=subset["username"],
                text=subset["display_name"],
                hovertemplate=(
                    "<b>%{text}</b><br>@%{customdata}<br>"
                    f"{category}<extra></extra>"
                ),
            )
        )

        if show_names:
            for _, row in subset.iterrows():
                if row["username"] == selected_username:
                    continue
                label_rows.append(
                    (
                        float(row["x"]) + label_offset,
                        float(row["y"]),
                        float(row.get("followers") or 0),
                        row,
                    )
                )

    if show_names and label_rows:
        extra = label_rows[1:] if len(label_rows) > 1 else label_rows
        if len(label_rows) > 1:
            kept = _filter_non_overlapping(
                [(x, y, pri) for x, y, pri, _ in extra],
                label_sep,
            )
            final_rows = [label_rows[0]] + [extra[i] for i in kept]
        else:
            final_rows = label_rows

        fig.add_trace(
            go.Scatter(
                x=[r[0] for r in final_rows],
                y=[r[1] for r in final_rows],
                mode="text",
                text=[str(r[3]["display_name"]) for r in final_rows],
                textfont=dict(
                    size=[
                        12 if str(r[3]["username"]) == selected_username else 10
                        for r in final_rows
                    ],
                    color=[
                        "#ffffff"
                        if str(r[3]["username"]) == selected_username
                        else "rgba(237,233,254,0.45)"
                        for r in final_rows
                    ],
                    family="Inter, sans-serif",
                ),
                textposition="middle left",
                hoverinfo="skip",
                showlegend=False,
            )
        )

        if selected_username and selected_username in view_df["username"].values:
            sel = view_df[view_df["username"] == selected_username].iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[sel["x"]],
                    y=[sel["y"]],
                    mode="markers",
                    marker=dict(
                        size=[28],
                        color="rgba(167,139,250,0.08)",
                        line=dict(width=1.5, color="rgba(196,181,253,0.55)"),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )


def count_plotted_creators(trace_frames: list[pd.DataFrame]) -> int:
    """Count creator rows represented in clickable map traces."""
    return sum(len(frame) for frame in trace_frames)


def build_creator_map_figure(
    df: pd.DataFrame,
    *,
    selected_username: str | None = None,
    height: int = MAP_HEIGHT,
    lod_tier: int | None = None,
    x_range: tuple[float, float] | None = None,
    y_range: tuple[float, float] | None = None,
    bounds: dict[str, list[float]] | None = None,
) -> tuple[go.Figure, list[pd.DataFrame], dict[int, int], int]:
    """Progressive-disclosure atlas map. Returns figure, trace frames, curve map, and tier."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=height,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig, [], {}, LOD_TIER_REGIONS

    plot_df = df.copy()
    map_bounds = bounds or compute_map_bounds(plot_df)
    if not x_range or not y_range:
        x_range = (map_bounds["x"][0], map_bounds["x"][1])
        y_range = (map_bounds["y"][0], map_bounds["y"][1])

    zoom_factor = compute_zoom_factor(map_bounds, x_range, y_range)
    tier = lod_tier if lod_tier is not None else infer_lod_tier(zoom_factor)

    color_map = _category_color_map(plot_df["category"].dropna().unique().tolist())
    trace_frames: list[pd.DataFrame] = []
    clickable_curves: dict[int, int] = {}

    fig = go.Figure()
    _add_grid(fig, map_bounds)

    if tier == LOD_TIER_REGIONS:
        _add_region_tier(fig, plot_df, color_map, x_range=x_range, y_range=y_range)
    else:
        _add_dots_tier(
            fig,
            plot_df,
            color_map,
            x_range=x_range,
            y_range=y_range,
            selected_username=selected_username,
            trace_frames=trace_frames,
            clickable_curves=clickable_curves,
            show_names=tier >= LOD_TIER_LABELS,
        )

    fig.update_layout(
        height=height,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f0ebff", "family": "Inter, sans-serif"},
        showlegend=False,
        xaxis=dict(
            range=list(x_range),
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False,
            visible=False,
        ),
        yaxis=dict(
            range=list(y_range),
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False,
            visible=False,
            scaleanchor="x",
            scaleratio=1,
        ),
        hovermode="closest",
        dragmode="pan",
        uirevision=f"creator-atlas-tier-{tier}",
    )
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=False)

    return fig, trace_frames, clickable_curves, tier


def username_from_map_selection(
    event,
    trace_frames: list[pd.DataFrame],
    clickable_curves: dict[int, int] | None = None,
) -> str | None:
    """Extract username from a Streamlit Plotly selection event."""
    if event is None or not getattr(event, "selection", None):
        return None

    points = event.selection.get("points", []) if isinstance(event.selection, dict) else event.selection.points
    if not points:
        return None

    point = points[0]
    custom = point.get("customdata")
    if custom:
        return str(custom)

    curve_number = point.get("curve_number", point.get("curveNumber"))
    point_index = point.get("point_index", point.get("pointIndex"))
    if curve_number is None or point_index is None:
        return None

    if clickable_curves and int(curve_number) in clickable_curves:
        frame_idx = clickable_curves[int(curve_number)]
        try:
            return str(trace_frames[frame_idx].iloc[int(point_index)]["username"])
        except (IndexError, ValueError, KeyError):
            return None

    return None
