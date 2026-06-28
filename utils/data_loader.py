"""Load and prepare creator data for the Streamlit app."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.paths import CREATORS_CSV
from utils.schema import CREATOR_COLUMNS, loads_json_list, validate_creators_df


@st.cache_data(show_spinner="Loading creators…")
def load_creators(csv_path: str | Path = CREATORS_CSV) -> pd.DataFrame:
    """Load creators.csv and parse JSON list columns."""
    return _load_creators_df(csv_path)


def _load_creators_df(csv_path: str | Path = CREATORS_CSV) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        return pd.DataFrame(columns=CREATOR_COLUMNS)

    df = pd.read_csv(path)
    errors = validate_creators_df(df)
    if errors:
        raise ValueError("Invalid creators CSV:\n" + "\n".join(f"- {e}" for e in errors))

    df = df.copy()
    df["recent_captions_list"] = df["recent_captions"].map(loads_json_list)
    df["hashtags_list"] = df["hashtags"].map(loads_json_list)
    df["caption_count"] = df["recent_captions_list"].map(len)
    df["hashtag_count"] = df["hashtags_list"].map(len)
    df["search_text"] = (
        df["display_name"].fillna("")
        + " "
        + df["username"].fillna("")
        + " "
        + df["bio"].fillna("")
        + " "
        + df["category"].fillna("")
    ).str.lower()

    return df


def format_followers(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    value = int(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def filter_creators(
    df: pd.DataFrame,
    *,
    query: str = "",
    categories: list[str] | None = None,
) -> pd.DataFrame:
    """Filter creators by search text and category."""
    filtered = df

    if categories:
        filtered = filtered[filtered["category"].isin(categories)]

    if query.strip():
        needle = query.strip().lower()
        filtered = filtered[filtered["search_text"].str.contains(needle, na=False)]

    return filtered.sort_values("followers", ascending=False, na_position="last")
