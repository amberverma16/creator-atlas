"""Creator dataset schema and validation helpers."""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

CREATOR_COLUMNS = [
    "creator_id",
    "username",
    "display_name",
    "bio",
    "category",
    "recent_captions",
    "hashtags",
    "followers",
    "avg_likes",
    "avg_views",
    "profile_url",
    "collected_at",
    "source",
]

SEED_COLUMNS = ["username", "category"]

MAX_RECENT_POSTS = 12
MIN_FOLLOWERS = 10_000
FOLLOWER_EXCEPTIONS = frozenset({"brownbindibaddie", "baboob.media"})
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._]{1,24}$")
GENERIC_DISPLAY_NAME_PATTERN = re.compile(r"^user\d+$", re.IGNORECASE)
FANPAGE_HINT_PATTERN = re.compile(r"fan\s*page", re.IGNORECASE)


def normalize_username(username: str) -> str:
    """Strip @ prefix and whitespace from a TikTok handle."""
    return username.strip().lstrip("@").lower()


def profile_url_for(username: str) -> str:
    return f"https://www.tiktok.com/@{normalize_username(username)}"


def is_follower_exception(username: str) -> bool:
    return normalize_username(username) in FOLLOWER_EXCEPTIONS


def is_generic_display_name(display_name: str) -> bool:
    return bool(GENERIC_DISPLAY_NAME_PATTERN.match(str(display_name).strip()))


def is_fanpage_display_name(display_name: str) -> bool:
    return bool(FANPAGE_HINT_PATTERN.search(str(display_name)))


def passes_quality_gate(
    username: str,
    display_name: str,
    followers: int | float | None,
) -> tuple[bool, str | None]:
    """Return (accepted, rejection_reason)."""
    handle = normalize_username(username)

    if is_generic_display_name(display_name):
        return False, "generic display name (likely wrong account)"

    if is_fanpage_display_name(display_name):
        return False, "fan page account"

    if is_follower_exception(handle):
        return True, None

    if followers is None or (isinstance(followers, float) and pd.isna(followers)):
        return False, f"missing follower count (minimum {MIN_FOLLOWERS:,})"

    if int(followers) < MIN_FOLLOWERS:
        return False, f"below {MIN_FOLLOWERS:,} followers ({int(followers):,})"

    return True, None


def filter_valid_creators(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Keep rows that pass follower and identity quality gates."""
    kept_rows: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for _, row in df.iterrows():
        accepted, reason = passes_quality_gate(
            str(row["username"]),
            str(row["display_name"]),
            row.get("followers"),
        )
        if accepted:
            kept_rows.append(row.to_dict())
        else:
            rejected.append(
                {
                    "username": str(row["username"]),
                    "display_name": str(row["display_name"]),
                    "followers": str(row.get("followers")),
                    "reason": reason or "failed quality gate",
                }
            )

    if not kept_rows:
        return pd.DataFrame(columns=CREATOR_COLUMNS), rejected

    return pd.DataFrame(kept_rows, columns=CREATOR_COLUMNS), rejected


def dumps_json_list(values: list[Any]) -> str:
    return json.dumps(values, ensure_ascii=False)


def loads_json_list(value: Any) -> list[Any]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return json.loads(text)
    raise ValueError(f"Expected JSON list string, got {type(value)!r}")


def validate_creators_df(df: pd.DataFrame) -> list[str]:
    """Return a list of validation error messages (empty if valid)."""
    errors: list[str] = []

    missing = [col for col in CREATOR_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
        return errors

    if df["creator_id"].duplicated().any():
        dupes = df.loc[df["creator_id"].duplicated(), "creator_id"].tolist()
        errors.append(f"Duplicate creator_id values: {dupes}")

    for idx, row in df.iterrows():
        username = str(row["username"])
        if not USERNAME_PATTERN.match(username):
            errors.append(f"Row {idx}: invalid username {username!r}")

        expected_url = profile_url_for(username)
        if str(row["profile_url"]) != expected_url:
            errors.append(f"Row {idx}: profile_url mismatch for @{username}")

        for json_col in ("recent_captions", "hashtags"):
            try:
                loads_json_list(row[json_col])
            except json.JSONDecodeError as exc:
                errors.append(f"Row {idx}: invalid JSON in {json_col}: {exc}")

    return errors
