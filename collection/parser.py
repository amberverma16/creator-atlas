"""Parse TikTok profile HTML and post payloads."""

from __future__ import annotations

import json
import re
from statistics import mean
from typing import Any

from utils.schema import MAX_RECENT_POSTS, dumps_json_list

REHYDRATION_PATTERN = re.compile(
    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
    re.DOTALL,
)
HASHTAG_PATTERN = re.compile(r"#([A-Za-z0-9_]+)")


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_profile_html(html: str) -> dict[str, Any]:
    match = REHYDRATION_PATTERN.search(html)
    if not match:
        return {"error": "embedded profile JSON not found"}

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {"error": "failed to decode embedded profile JSON"}

    user_detail = payload.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
    if user_detail.get("statusCode") not in (None, 0):
        return {"error": user_detail.get("statusMsg") or "profile unavailable"}

    user_info = user_detail.get("userInfo") or {}
    user = user_info.get("user") or {}
    stats = user_info.get("statsV2") or user_info.get("stats") or {}

    unique_id = user.get("uniqueId")
    if not unique_id:
        return {"error": "profile not found or is private"}

    return {
        "username": unique_id,
        "display_name": user.get("nickname") or unique_id,
        "bio": user.get("signature") or "",
        "followers": _safe_int(stats.get("followerCount")),
        "sec_uid": user.get("secUid"),
        "posts": [],
    }


def parse_posts_payload(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []

    items = payload.get("itemList") or []
    posts: list[dict[str, Any]] = []

    for item in items[:MAX_RECENT_POSTS]:
        stats = item.get("statsV2") or item.get("stats") or {}
        posts.append(
            {
                "caption": item.get("desc") or "",
                "likes": _safe_int(stats.get("diggCount")),
                "views": _safe_int(stats.get("playCount")),
            }
        )

    return posts


def extract_hashtags(captions: list[str]) -> list[str]:
    seen: set[str] = set()
    tags: list[str] = []

    for caption in captions:
        for tag in HASHTAG_PATTERN.findall(caption):
            normalized = tag.lower()
            if normalized not in seen:
                seen.add(normalized)
                tags.append(normalized)

    return tags


def aggregate_posts(posts: list[dict[str, Any]]) -> dict[str, Any]:
    captions = [post["caption"] for post in posts if post.get("caption")]
    likes = [post["likes"] for post in posts if post.get("likes") is not None]
    views = [post["views"] for post in posts if post.get("views") is not None]

    return {
        "recent_captions": dumps_json_list(captions),
        "hashtags": dumps_json_list(extract_hashtags(captions)),
        "avg_likes": round(mean(likes), 2) if likes else None,
        "avg_views": round(mean(views), 2) if views else None,
        "post_count": len(posts),
    }


def build_creator_row(
    *,
    username: str,
    category: str,
    profile: dict[str, Any],
    collected_at: str,
    source: str,
) -> dict[str, Any]:
    posts = profile.get("posts") or []
    aggregates = aggregate_posts(posts)

    return {
        "creator_id": username.lower(),
        "username": username,
        "display_name": profile.get("display_name") or username,
        "bio": profile.get("bio") or "",
        "category": category,
        "recent_captions": aggregates["recent_captions"],
        "hashtags": aggregates["hashtags"],
        "followers": profile.get("followers"),
        "avg_likes": aggregates["avg_likes"],
        "avg_views": aggregates["avg_views"],
        "profile_url": f"https://www.tiktok.com/@{username}",
        "collected_at": collected_at,
        "source": source,
    }
