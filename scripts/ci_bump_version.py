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
    """
    Bumps the patch version of the specified package in its pyproject.toml file.

    Args:
        package: The name of the package to bump.

    Raises:
        FileNotFoundError: If the pyproject.toml file does not exist.
        ValueError: If the version string is not in the format X.Y.Z.
    """
    pyproject = Path(f"packages/{package}/pyproject.toml")

    if not pyproject.exists():
        raise FileNotFoundError(f"File not found: {pyproject}")

    data = tomllib.loads(pyproject.read_text())
    current = data["project"]["version"]

    try:
        major, minor, patch = map(int, current.split("."))
    except ValueError:
        raise ValueError(f"Invalid version format: {current}. Expected format: X.Y.Z")

    new = f"{major}.{minor}.{patch + 1}"
    data["project"]["version"] = new

    pyproject.write_text(tomllib.dumps(data))

    print(f"{package}: {current} -> {new}")


def main() -> None:
    """
    Entry point for the script. Parses command line arguments and executes the bump function.
    """
    if len(sys.argv) < 2:
        print("Usage: ci_bump_version.py <package> [package...]")
        sys.exit(1)

    for package in sys.argv[1:]:
        try:
            bump(package)
        except Exception as e:
            print(f"Error bumping package '{package}': {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()