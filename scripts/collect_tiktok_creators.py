#!/usr/bin/env python3
"""Collect public TikTok creator data from a curated seed list."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collection.fetcher import TikTokFetcher
from collection.parser import build_creator_row
from utils.paths import COLLECTION_REPORT_JSON, CREATORS_CSV, SEEDS_CSV, ensure_data_dirs
from utils.schema import (
    CREATOR_COLUMNS,
    SEED_COLUMNS,
    filter_valid_creators,
    normalize_username,
    passes_quality_gate,
)


def load_seeds(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [col for col in SEED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Seed file missing columns: {missing}")

    df = df.copy()
    df["username"] = df["username"].map(normalize_username)
    if df["username"].duplicated().any():
        dupes = df.loc[df["username"].duplicated(), "username"].tolist()
        raise ValueError(f"Duplicate usernames in seed file: {dupes}")

    return df


def load_existing_creators(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=CREATOR_COLUMNS)
    return pd.read_csv(path)


def merge_creator_rows(existing: pd.DataFrame, new_rows: list[dict]) -> pd.DataFrame:
    if not new_rows:
        return existing

    incoming = pd.DataFrame(new_rows, columns=CREATOR_COLUMNS)
    if existing.empty:
        combined = incoming
    else:
        combined = pd.concat([existing, incoming], ignore_index=True)

    combined["creator_id"] = combined["username"].map(normalize_username)
    combined = combined.drop_duplicates(subset=["creator_id"], keep="last")
    return combined[CREATOR_COLUMNS]


def collect_one(
    fetcher: TikTokFetcher,
    username: str,
    category: str,
    *,
    skip_quality_gate: bool = False,
) -> tuple[dict | None, str | None]:
    result = fetcher.fetch_creator(username)
    if result.error:
        return None, result.error

    profile = result.posts_json or {}
    if not profile.get("username"):
        return None, "profile parsed but username missing"

    source = "scrape" if profile.get("posts") else "mixed"
    row = build_creator_row(
        username=profile["username"],
        category=category,
        profile=profile,
        collected_at=date.today().isoformat(),
        source=source,
    )

    if not skip_quality_gate:
        accepted, reason = passes_quality_gate(
            row["username"],
            row["display_name"],
            row["followers"],
        )
        if not accepted:
            return None, reason

    return row, None


def run_collection(
    *,
    seeds_path: Path,
    output_path: Path,
    report_path: Path,
    limit: int | None,
    username: str | None,
    usernames: list[str] | None,
    delay: float,
    dry_run: bool,
    merge: bool,
    skip_quality_gate: bool,
) -> dict:
    ensure_data_dirs()
    seeds = load_seeds(seeds_path)

    if username:
        seeds = seeds[seeds["username"] == normalize_username(username)]
        if seeds.empty:
            raise ValueError(f"Username not found in seeds: {username}")
    elif usernames:
        normalized = {normalize_username(u) for u in usernames}
        seeds = seeds[seeds["username"].isin(normalized)]
        if seeds.empty:
            raise ValueError(f"No matching usernames found in seeds: {usernames}")
    elif limit is not None:
        seeds = seeds.head(limit)

    report: dict = {
        "seeds_path": str(seeds_path),
        "output_path": str(output_path),
        "total_seeds": len(seeds),
        "success": 0,
        "failed": 0,
        "failures": [],
        "rows": [],
    }

    rows: list[dict] = []

    with TikTokFetcher(delay_seconds=delay) as fetcher:
        for _, seed in seeds.iterrows():
            handle = seed["username"]
            category = seed["category"]
            print(f"Collecting @{handle} ({category})...", flush=True)

            row, error = collect_one(
                fetcher,
                handle,
                category,
                skip_quality_gate=skip_quality_gate,
            )
            if error:
                report["failed"] += 1
                report["failures"].append({"username": handle, "reason": error})
                print(f"  failed: {error}", flush=True)
                continue

            report["success"] += 1
            rows.append(row)
            post_count = json.loads(row["recent_captions"])
            print(
                f"  ok: {row['display_name']} | followers={row['followers']} | posts={len(post_count)}",
                flush=True,
            )

    report["rows"] = [row["username"] for row in rows]

    if dry_run:
        print(f"Dry run complete: {report['success']} succeeded, {report['failed']} failed.")
        return report

    if rows:
        if merge:
            existing = load_existing_creators(output_path)
            df = merge_creator_rows(existing, rows)
        else:
            df = pd.DataFrame(rows, columns=CREATOR_COLUMNS)

        if skip_quality_gate:
            filtered_df = df
            rejected = []
        else:
            filtered_df, rejected = filter_valid_creators(df)
            if rejected:
                report["filtered_existing"] = rejected

        output_path.parent.mkdir(parents=True, exist_ok=True)
        filtered_df.to_csv(output_path, index=False)
        print(f"\nWrote {len(filtered_df)} creators to {output_path}")
        if rejected:
            print(f"Filtered out {len(rejected)} rows that failed quality gates.")
    else:
        print("\nNo creators collected; CSV was not updated.")

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote collection report to {report_path}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=SEEDS_CSV)
    parser.add_argument("--output", type=Path, default=CREATORS_CSV)
    parser.add_argument("--report", type=Path, default=COLLECTION_REPORT_JSON)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N seeds")
    parser.add_argument("--username", type=str, default=None, help="Process a single username")
    parser.add_argument(
        "--usernames",
        nargs="+",
        default=None,
        help="Process multiple usernames from the seed file",
    )
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds to wait between creators")
    parser.add_argument("--merge", action="store_true", help="Merge results into existing CSV")
    parser.add_argument(
        "--no-quality-gate",
        action="store_true",
        help="Skip follower and identity quality filters",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_collection(
        seeds_path=args.seeds,
        output_path=args.output,
        report_path=args.report,
        limit=args.limit,
        username=args.username,
        usernames=args.usernames,
        delay=args.delay,
        dry_run=args.dry_run,
        merge=args.merge,
        skip_quality_gate=args.no_quality_gate,
    )
    if report["failed"] and report["success"] == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
