#!/usr/bin/env python3

"""
TEMPORARY

Automatically bumps the patch version of one or more packages.

Reason:
    During rapid platform development we don't want to manually edit
    pyproject.toml before every release.

TODO:
    Remove this script once `aip release` owns the versioning workflow.
"""

from pathlib import Path
import sys
import tomllib


def bump(package: str) -> None:
    pyproject = Path(f"packages/{package}/pyproject.toml")

    if not pyproject.exists():
        raise FileNotFoundError(pyproject)

    text = pyproject.read_text()
    data = tomllib.loads(text)

    current = data["project"]["version"]

    major, minor, patch = map(int, current.split("."))

    new = f"{major}.{minor}.{patch + 1}"

    text = text.replace(
        f'version = "{current}"',
        f'version = "{new}"',
        1,
    )

    pyproject.write_text(text)

    print(f"{package}: {current} -> {new}")


def main():
    if len(sys.argv) < 2:
        print("Usage: bump_version.py <package> [package...]")
        sys.exit(1)

    for package in sys.argv[1:]:
        bump(package)


if __name__ == "__main__":
    main()
