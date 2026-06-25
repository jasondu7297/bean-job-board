#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jobboard.pipeline import run  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Celina's personal new-grad job board.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Build from the verified starter snapshot without making network requests.",
    )
    parser.add_argument("--max-age-days", type=int, default=None, help="Maximum age for dated live jobs.")
    parser.add_argument("--min-score", type=int, default=None, help="Minimum resume-fit score to publish.")
    parser.add_argument("--verbose", action="store_true", help="Show detailed source logs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    board = run(
        ROOT,
        offline=args.offline,
        max_age_days=args.max_age_days,
        min_score=args.min_score,
    )
    print(
        f"Published {board['meta']['total_jobs']} jobs "
        f"({board['meta']['strong_matches']} strong matches; "
        f"{board['meta']['research_jobs']} research roles)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
