"""Autonomous extractor promotion engine for Canonica.

Promotes AI-generated extractors from staging (.canonica/generated/) into the
production package (aip_canonica/extractors/<category>/) with thread-safe and
process-safe locking, AST validation, automated registration, and code formatting.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager
import fcntl
import importlib
import logging
from pathlib import Path
import re
import subprocess
import threading

logger = logging.getLogger(__name__)

# Process-level reentrant lock for thread safety in multi-threaded application servers
_PROMOTION_THREAD_LOCK = threading.RLock()


@contextmanager
def promotion_lock(lock_file_path: Path):
    """Context manager providing both thread-level and OS-level file locking.

    Ensures that concurrent service workers or background processes cannot race,
    overwrite, or read partially written extractor files or the registry.
    """
    with _PROMOTION_THREAD_LOCK:
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_file_path, "a") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)


def find_extractor_class_name(code: str) -> str | None:
    """Inspect Python code AST to identify the primary Extractor class name."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.endswith("Extractor") or "Extractor" in [
                    base.id for base in node.bases if isinstance(base, ast.Name)
                ]:
                    return node.name
        # Fallback to any class ending with Extractor via regex
        m = re.search(r"class\s+([A-Za-z0-9_]+Extractor)\b", code)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def register_extractor_in_registry(
    registry_file: Path,
    category: str,
    module_slug: str,
    class_name: str,
) -> bool:
    """Safely update registry.py to import and register the promoted extractor.

    Returns True if registry was updated, False if already registered.
    """
    content = registry_file.read_text(encoding="utf-8")
    import_stmt = f"from aip_canonica.extractors.{category}.{module_slug} import {class_name}"
    instantiation = f"{class_name}()"

    if import_stmt in content and instantiation in content:
        return False

    lines = content.splitlines()

    # 1. Insert import statement with other extractor imports
    if import_stmt not in content:
        last_extractor_import_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith("from aip_canonica.extractors."):
                last_extractor_import_idx = idx
        if last_extractor_import_idx != -1:
            lines.insert(last_extractor_import_idx + 1, import_stmt)
        else:
            lines.insert(0, import_stmt)

    updated_content = "\n".join(lines)

    # 2. Insert instantiation into default registry list
    if instantiation not in updated_content:
        # Locate the _DEFAULT_REGISTRY initialization list
        pattern = r"(ExtractorRegistry\(\s*\[\s*)(.*?)(\s*\]\s*\))"
        match = re.search(pattern, updated_content, re.DOTALL)
        if match:
            existing_items = match.group(2).rstrip()
            existing_items = re.sub(r",\s*$", "", existing_items)
            separator = ",\n                " if existing_items else "\n                "
            new_list_body = f"{existing_items}{separator}{instantiation},\n            "
            updated_content = (
                updated_content[: match.start(2)]
                + new_list_body
                + updated_content[match.end(2) :]
            )

    registry_file.write_text(updated_content + "\n", encoding="utf-8")
    try:
        subprocess.run(["uv", "run", "ruff", "format", str(registry_file)], check=False, capture_output=True)
    except Exception:
        pass
    return True


def promote_extractor(
    source_path: str | Path,
    *,
    category: str = "bank",
    target_name: str | None = None,
    extractors_root: Path | None = None,
    auto_register: bool = True,
    format_code: bool = True,
) -> Path:
    """Promote an AI-generated extractor into the production extractors package.

    Thread-safe and process-safe.
    """
    src = Path(source_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Generated extractor file not found: {src}")

    code = src.read_text(encoding="utf-8")
    class_name = find_extractor_class_name(code)
    if not class_name:
        raise ValueError(f"Could not find an Extractor class in '{src.name}'.")

    # Determine base packages directory
    if extractors_root is None:
        # Default to aip_canonica/src/aip_canonica/extractors
        module_path = Path(__file__).resolve()
        extractors_root = module_path.parent / "extractors"

    category_dir = extractors_root / category
    registry_file = extractors_root / "registry.py"
    lock_file = extractors_root / ".promotion.lock"

    if target_name:
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", target_name.lower()).strip("_")
    else:
        # Derive from source file: e.g. axis_statement_strategy_extractor -> axis
        raw_stem = src.stem
        raw_stem = re.sub(r"_(?:strategy_)?extractor$", "", raw_stem)
        raw_stem = re.sub(r"_statement$", "", raw_stem)
        slug = raw_stem

    target_file = category_dir / f"{slug}.py"

    with promotion_lock(lock_file):
        category_dir.mkdir(parents=True, exist_ok=True)

        # Write the promoted code
        target_file.write_text(code, encoding="utf-8")
        logger.info("[Promotion] Wrote promoted extractor to: %s", target_file)

        # Register in registry.py
        if auto_register and registry_file.exists():
            updated = register_extractor_in_registry(
                registry_file=registry_file,
                category=category,
                module_slug=slug,
                class_name=class_name,
            )
            if updated:
                logger.info(
                    "[Promotion] Registered '%s' in ExtractorRegistry (%s)",
                    class_name,
                    registry_file,
                )

        # Invalidate in-memory cached registry
        try:
            from aip_canonica.extractors import registry

            registry._DEFAULT_REGISTRY = None
        except Exception:
            pass

        # Optional code formatting via ruff
        if format_code:
            try:
                subprocess.run(
                    ["uv", "run", "ruff", "check", "--fix", "--unsafe-fixes", str(target_file)],
                    check=False,
                    capture_output=True,
                )
                subprocess.run(
                    ["uv", "run", "ruff", "format", str(target_file)],
                    check=False,
                    capture_output=True,
                )
            except Exception:
                pass

        # Verify python syntax and importability
        try:
            importlib.invalidate_caches()
            importlib.import_module(f"aip_canonica.extractors.{category}.{slug}")
        except Exception as exc:
            logger.warning("[Promotion] Import check warning for %s: %s", slug, exc)

    return target_file
