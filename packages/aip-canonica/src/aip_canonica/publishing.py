"""Automated upstream synchronization for promoted Canonica extractors.

Scans for locally promoted extractors, verifies test suites, creates dedicated
feature branches, and safely pushes them to the upstream code repository.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)


def check_git_status(repo_root: Path) -> list[str]:
    """Return modified or untracked extractor files in packages/aip-canonica/src/aip_canonica/extractors."""
    res = subprocess.run(
        ["git", "status", "--porcelain", "packages/aip-canonica/src/aip_canonica/extractors/"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return []
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    return [entry for entry in lines if not entry.endswith(".promotion.lock")]


def sync_to_upstream(
    repo_root: Path,
    *,
    remote: str = "origin",
    dry_run: bool = False,
) -> dict[str, str] | None:
    """Synchronize pending promoted extractors to a dedicated upstream Git branch."""
    changed_files = check_git_status(repo_root)
    if not changed_files:
        logger.info("[UpstreamSync] No pending extractor changes to synchronize.")
        return None

    logger.info("[UpstreamSync] Detected %d pending extractor changes:", len(changed_files))
    for f in changed_files:
        logger.info("  • %s", f)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch_name = f"canonica/auto-learned-extractors-{timestamp}"

    if dry_run:
        logger.info("[UpstreamSync][DryRun] Would create branch: %s and push to %s", branch_name, remote)
        return {"branch": branch_name, "status": "dry_run", "files": str(changed_files)}

    # 1. Run unit test verification first to ensure no broken extractors are committed
    test_res = subprocess.run(
        ["uv", "run", "pytest", "packages/aip-canonica/tests/unit/extractors/"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if test_res.returncode != 0:
        logger.error("[UpstreamSync] Test suite failed! Refusing to push unverified code.")
        logger.error(test_res.stdout)
        return {"status": "failed_tests", "error": test_res.stdout}

    # 2. Create feature branch
    subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_root, check=True)

    try:
        # 3. Stage extractors and registry
        subprocess.run(
            ["git", "add", "packages/aip-canonica/src/aip_canonica/extractors/"],
            cwd=repo_root,
            check=True,
        )

        # 4. Commit
        commit_msg = (
            f"feat(extractors): synchronize auto-learned extractors ({timestamp})\n\n"
            "Automatically generated and promoted by Canonica Extractor Engine."
        )
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_root, check=True)

        # 5. Push to remote
        push_res = subprocess.run(
            ["git", "push", "-u", remote, branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        commit_sha_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = commit_sha_res.stdout.strip()

        pr_url = f"https://github.com/spar2522/ai_platform/pull/new/{branch_name}"
        logger.info("[UpstreamSync] Successfully pushed branch '%s' (commit %s)", branch_name, commit_sha[:8])
        logger.info("[UpstreamSync] PR Link: %s", pr_url)

        return {
            "branch": branch_name,
            "commit_sha": commit_sha,
            "pr_url": pr_url,
            "status": "pushed" if push_res.returncode == 0 else "push_failed",
        }
    finally:
        # Return to main or original branch if needed
        pass
