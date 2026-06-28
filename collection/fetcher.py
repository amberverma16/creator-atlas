"""Fetch public TikTok profile pages and post lists."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx

from utils.schema import normalize_username

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REHYDRATION_PATTERN = re.compile(
    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
    re.DOTALL,
)


@dataclass
class FetchResult:
    username: str
    profile_html: str | None = None
    posts_json: dict | None = None
    error: str | None = None


class TikTokFetcher:
    """Lightweight HTTP client for public TikTok profile data."""

    def __init__(self, delay_seconds: float = 3.0) -> None:
        self.delay_seconds = delay_seconds
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> TikTokFetcher:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def fetch_profile(self, username: str) -> FetchResult:
        username = normalize_username(username)
        url = f"https://www.tiktok.com/@{username}"
        headers = {**DEFAULT_HEADERS, "Referer": url}

        try:
            response = self._client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return FetchResult(username=username, error=f"profile request failed: {exc}")

        if not REHYDRATION_PATTERN.search(response.text):
            return FetchResult(
                username=username,
                error="profile page loaded but embedded data was not found",
            )

        return FetchResult(username=username, profile_html=response.text)

    def fetch_posts(self, username: str, sec_uid: str) -> dict | None:
        username = normalize_username(username)
        headers = {
            **DEFAULT_HEADERS,
            "Referer": f"https://www.tiktok.com/@{username}",
        }
        params = {
            "secUid": sec_uid,
            "count": 12,
            "cursor": 0,
            "type": 1,
            "device_platform": "webapp",
            "aid": 1988,
        }

        try:
            response = self._client.get(
                "https://www.tiktok.com/api/creator/item_list/",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            if not response.text:
                return None
            return response.json()
        except (httpx.HTTPError, ValueError):
            return None

    def fetch_creator(self, username: str) -> FetchResult:
        result = self.fetch_profile(username)
        if result.error or not result.profile_html:
            return result

        from collection.parser import parse_profile_html, parse_posts_payload

        profile = parse_profile_html(result.profile_html)
        if profile.get("error"):
            result.error = profile["error"]
            return result

        sec_uid = profile.get("sec_uid")
        if sec_uid:
            posts_payload = self.fetch_posts(username, sec_uid)
            profile["posts"] = parse_posts_payload(posts_payload)
        else:
            profile["posts"] = []

        result.posts_json = profile
        time.sleep(self.delay_seconds)
        return result
