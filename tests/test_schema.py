"""Tests for creator quality gates."""

from utils.schema import (
    MIN_FOLLOWERS,
    passes_quality_gate,
)


def test_follower_exception_allows_small_accounts() -> None:
    accepted, reason = passes_quality_gate("brownbindibaddie", "ambs", 7040)
    assert accepted is True
    assert reason is None

    accepted, reason = passes_quality_gate("baboob", "BaboOB", 6)
    assert accepted is True
    assert reason is None


def test_high_follower_wrong_identity_still_passes_gate() -> None:
    """Follower count alone cannot catch impersonators — seed curation handles that."""
    accepted, reason = passes_quality_gate("speed", "Gevo", 11858)
    assert accepted is True
    assert reason is None


def test_generic_display_name_is_rejected() -> None:
    accepted, reason = passes_quality_gate("wisdomkaye", "user43148870288", 42)
    assert accepted is False
    assert "generic display name" in reason
