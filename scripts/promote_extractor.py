#!/usr/bin/env python3
"""CLI utility to promote an AI-generated extractor into the canonical extractors package."""

import argparse
import logging
from pathlib import Path
import sys

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "packages" / "aip-canonica" / "src"))

from aip_canonica.promotion import promote_extractor  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote an AI-generated extractor into the production package."
    )
    parser.add_argument(
        "--source",
        "-s",
        required=True,
        type=str,
        help="Path to generated extractor file (e.g. .canonica/generated/axis_extractor.py)",
    )
    parser.add_argument(
        "--category",
        "-c",
        default="bank",
        type=str,
        help="Extractor category (bank, invoice, ledger). Default: bank",
    )
    parser.add_argument(
        "--target-name",
        "-t",
        default=None,
        type=str,
        help="Optional module name for the promoted file (e.g. 'axis')",
    )

    args = parser.parse_args()
    source_file = Path(args.source)
    if not source_file.exists():
        print(f"Error: Source file does not exist: {source_file}", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print("  CANONICA EXTRACTOR PROMOTION ENGINE")
    print(f"  • Source:   {source_file}")
    print(f"  • Category: {args.category}")
    print("=" * 70)

    try:
        target = promote_extractor(
            source_path=source_file,
            category=args.category,
            target_name=args.target_name,
        )
        print("\n✔ Extractor successfully promoted and registered!")
        print(f"  Destination: {target}")
        print("  Status: Thread-safe locked, formatted, and registered in ExtractorRegistry.\n")
    except Exception as exc:
        print(f"\n✖ Promotion failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
