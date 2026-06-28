"""Text construction helpers for downstream embedding pipeline."""

from __future__ import annotations


def build_embedding_text(
    *,
    display_name: str,
    username: str,
    category: str,
    bio: str,
    captions: list[str],
    hashtags: list[str],
    max_captions: int = 5,
) -> str:
    """Build a consistent text blob for embedding models (Milestone 2)."""
    caption_sample = " | ".join(captions[:max_captions])
    hashtag_sample = ", ".join(hashtags[:20])
    parts = [
        f"{display_name} (@{username})",
        category,
        bio.strip(),
    ]
    if caption_sample:
        parts.append(f"Recent: {caption_sample}")
    if hashtag_sample:
        parts.append(f"Hashtags: {hashtag_sample}")
    return " | ".join(part for part in parts if part)
