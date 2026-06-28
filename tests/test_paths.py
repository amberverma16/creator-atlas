"""Tests for path utilities."""

from utils.paths import DATA_DIR, DATA_PROCESSED_DIR, DATA_RAW_DIR, PROJECT_ROOT


def test_project_root_exists() -> None:
    assert PROJECT_ROOT.is_dir()


def test_data_directories_are_under_project_root() -> None:
    assert DATA_DIR == PROJECT_ROOT / "data"
    assert DATA_RAW_DIR == DATA_DIR / "raw"
    assert DATA_PROCESSED_DIR == DATA_DIR / "processed"
