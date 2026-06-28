"""Tests for creator data loading."""

from utils.data_loader import _load_creators_df, filter_creators, format_followers
from utils.paths import CREATORS_CSV


def test_load_creators_returns_rows() -> None:
    df = _load_creators_df(CREATORS_CSV)
    assert len(df) > 0
    assert "recent_captions_list" in df.columns


def test_format_followers() -> None:
    assert format_followers(1_500_000) == "1.5M"
    assert format_followers(12_500) == "12.5K"
    assert format_followers(None) == "—"


def test_filter_creators_by_category() -> None:
    df = _load_creators_df(CREATORS_CSV)
    filtered = filter_creators(df, categories=["Dance"])
    assert not filtered.empty
    assert (filtered["category"] == "Dance").all()
