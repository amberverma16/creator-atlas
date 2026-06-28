#!/usr/bin/env python3
"""Filter an existing creators CSV to valid rows only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.paths import COLLECTION_REPORT_JSON, CREATORS_CSV
from utils.schema import CREATOR_COLUMNS, filter_valid_creators


def main() -> None:
    if not CREATORS_CSV.exists():
        print(f"Missing file: {CREATORS_CSV}")
        sys.exit(1)

    df = pd.read_csv(CREATORS_CSV)
    filtered_df, rejected = filter_valid_creators(df)
    filtered_df.to_csv(CREATORS_CSV, index=False)

    report = {
        "input_rows": len(df),
        "output_rows": len(filtered_df),
        "rejected": rejected,
    }
    COLLECTION_REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Filtered {CREATORS_CSV}: {len(df)} -> {len(filtered_df)} rows")
    if rejected:
        print("\nRejected rows:")
        for item in rejected:
            print(
                f"  @{item['username']} ({item['followers']} followers): {item['reason']}"
            )


if __name__ == "__main__":
    main()
