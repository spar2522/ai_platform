#!/usr/bin/env python3
"""Background sync job to upload newly promoted extractors upstream to GitHub.

Can be run once or as a recurring daemon (e.g. hourly cron job).
"""

import argparse
import logging
from pathlib import Path
import sys
import time

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "packages" / "aip-canonica" / "src"))

from aip_canonica.publishing import sync_to_upstream  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_upstream")


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize promoted extractors upstream to GitHub.")
    parser.add_argument("--remote", default="origin", help="Git remote name (default: origin)")
    parser.add_argument("--dry-run", action="store_true", help="Inspect pending extractors without pushing")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously as a daemon, checking periodically (e.g. hourly)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Daemon interval in seconds (default: 3600s / 1 hour)",
    )

    args = parser.parse_args()

    if args.daemon:
        logger.info("Starting Canonica Upstream Sync Daemon (interval: %d seconds)...", args.interval)
        while True:
            try:
                sync_to_upstream(repo_root, remote=args.remote, dry_run=args.dry_run)
            except Exception as exc:
                logger.error("Daemon cycle encountered error: %s", exc)
            time.sleep(args.interval)
    else:
        result = sync_to_upstream(repo_root, remote=args.remote, dry_run=args.dry_run)
        if result:
            print("\nResult:", result)


if __name__ == "__main__":
    main()
