#!/usr/bin/env python3
"""Validate the creators CSV schema."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.paths import CREATORS_CSV
from utils.schema import validate_creators_df


def main() -> None:
    if not CREATORS_CSV.exists():
        print(f"Missing file: {CREATORS_CSV}")
        sys.exit(1)

    df = pd.read_csv(CREATORS_CSV)
    errors = validate_creators_df(df)

    print(f"Rows: {len(df)}")
    print(f"Categories: {df['category'].nunique()}")

    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("\nValidation passed.")


if __name__ == "__main__":
    main()
