import argparse
from pathlib import Path

PACKAGE_FILES = {
    "README.md": "# {title}\n\nPackage description.\n",
    "pyproject.toml": """[project]
name = "{package}"
version = "0.1.0"
requires-python = ">=3.11"
description = "{title}"
""",
    "src/{module}/__init__.py": "",
    "tests/__init__.py": "",
}


def create_package(name: str):
    root = Path("packages") / name
    module = name.replace("-", "_")

    directories = [
        root / "src" / module,
        root / "tests",
        root / "examples",
    ]

    for d in directories:
        d.mkdir(parents=True, exist_ok=True)

    for rel_path, template in PACKAGE_FILES.items():
        rel = rel_path.format(module=module)
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                template.format(package=name, title=name.replace("-", " ").title()),
                encoding="utf-8",
            )

    print(f"✅ Created package: {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("package_name", help="Example: ai-provider")
    args = parser.parse_args()
    create_package(args.package_name)
