"""Filesystem paths used across the application."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_SEEDS_DIR = DATA_DIR / "seeds"
CREATORS_CSV = DATA_DIR / "creators.csv"
SEEDS_CSV = DATA_SEEDS_DIR / "tiktok_creators.csv"
COLLECTION_REPORT_JSON = DATA_DIR / "collection_report.json"
EMBEDDINGS_PARQUET = DATA_PROCESSED_DIR / "embeddings.parquet"


def ensure_data_dirs() -> None:
    """Create data directories if they do not exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_SEEDS_DIR.mkdir(parents=True, exist_ok=True)
