#!/usr/bin/env python3
"""Build creator embeddings from data/creators.csv."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import EMBEDDING_MODEL
from utils.embeddings import build_embeddings_from_csv
from utils.paths import CREATORS_CSV, DATA_PROCESSED_DIR, EMBEDDINGS_PARQUET, ensure_data_dirs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=CREATORS_CSV)
    parser.add_argument("--output", type=Path, default=EMBEDDINGS_PARQUET)
    parser.add_argument("--model", type=str, default=EMBEDDING_MODEL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_data_dirs()

    if not args.input.exists():
        print(f"Missing input file: {args.input}")
        sys.exit(1)

    print(f"Building embeddings with {args.model}...")
    df = build_embeddings_from_csv(args.input, model_name=args.model)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output, index=False)

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "creator_count": len(df),
        "embedding_dim": int(df["embedding_dim"].iloc[0]),
        "input_csv": str(args.input),
        "output_parquet": str(args.output),
    }
    manifest_path = DATA_PROCESSED_DIR / "embeddings_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {len(df)} embeddings to {args.output}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
