#!/usr/bin/env python3
"""Build 2D map coordinates from creator embeddings using UMAP."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import UMAP_METRIC, UMAP_MIN_DIST, UMAP_N_NEIGHBORS, UMAP_RANDOM_STATE
from utils.map import build_map_coords
from utils.paths import (
    CREATORS_CSV,
    DATA_PROCESSED_DIR,
    EMBEDDINGS_PARQUET,
    MAP_COORDS_PARQUET,
    ensure_data_dirs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embeddings", type=Path, default=EMBEDDINGS_PARQUET)
    parser.add_argument("--creators", type=Path, default=CREATORS_CSV)
    parser.add_argument("--output", type=Path, default=MAP_COORDS_PARQUET)
    parser.add_argument("--n-neighbors", type=int, default=UMAP_N_NEIGHBORS)
    parser.add_argument("--min-dist", type=float, default=UMAP_MIN_DIST)
    parser.add_argument("--metric", type=str, default=UMAP_METRIC)
    parser.add_argument("--random-state", type=int, default=UMAP_RANDOM_STATE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_data_dirs()

    if not args.embeddings.exists():
        print(f"Missing embeddings file: {args.embeddings}")
        print("Run: python scripts/build_embeddings.py")
        sys.exit(1)

    effective_neighbors = min(args.n_neighbors, max(1, len(pd.read_parquet(args.embeddings)) - 1))
    print(
        f"Running UMAP (n_neighbors={effective_neighbors}, min_dist={args.min_dist}, "
        f"metric={args.metric})..."
    )

    map_df = build_map_coords(
        args.embeddings,
        args.creators,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist,
        metric=args.metric,
        random_state=args.random_state,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    map_df.to_parquet(args.output, index=False)

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "creator_count": len(map_df),
        "n_neighbors": effective_neighbors,
        "min_dist": args.min_dist,
        "metric": args.metric,
        "random_state": args.random_state,
        "x_range": [float(map_df["x"].min()), float(map_df["x"].max())],
        "y_range": [float(map_df["y"].min()), float(map_df["y"].max())],
        "embeddings_input": str(args.embeddings),
        "output_parquet": str(args.output),
    }
    manifest_path = DATA_PROCESSED_DIR / "map_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {len(map_df)} map coordinates to {args.output}")
    print(f"X range: {manifest['x_range'][0]:.2f} → {manifest['x_range'][1]:.2f}")
    print(f"Y range: {manifest['y_range'][0]:.2f} → {manifest['y_range'][1]:.2f}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
