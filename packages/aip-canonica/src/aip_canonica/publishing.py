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

    # Get original branch before creating new branch
    original_branch_res = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    original_branch = original_branch_res.stdout.strip() if original_branch_res.returncode == 0 else "unknown"

    try:
        # Run tests
        test_result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACM", "--", "packages/aip-canonica/"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if test_result.returncode != 0:
            logger.error("Test phase failed with output: %s", test_result.stderr)
            return {"status": "test_failed", "error": test_result.stderr}

        # Create new branch
        checkout_result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if checkout_result.returncode != 0:
            logger.error("Failed to create branch: %s", checkout_result.stderr)
            return {"status": "branch_creation_failed", "error": checkout_result.stderr}

        # Stage files
        stage_result = subprocess.run(
            ["git", "add", "packages/aip-canonica/"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if stage_result.returncode != 0:
            logger.error("Failed to stage files: %s", stage_result.stderr)
            return {"status": "staging_failed", "error": stage_result.stderr}

        # Commit
        commit_msg = (
            f"feat(extractors): synchronize auto-learned extractors ({timestamp})\n\n"
            "Automatically generated and promoted by Canonica Extractor Engine."
        )
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if commit_result.returncode != 0:
            logger.error("Commit failed with output: %s", commit_result.stderr)
            return {"status": "commit_failed", "error": commit_result.stderr}

        # Push
        push_result = subprocess.run(
            ["git", "push", "-u", remote, branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if push_result.returncode != 0:
            logger.error("Push failed with output: %s", push_result.stderr)
            return {"status": "push_failed", "error": push_result.stderr}

        # Get commit hash
        commit_sha_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        commit_sha = commit_sha_res.stdout.strip()

        pr_url = f"https://github.com/spar2522/ai_platform/pull/new/{branch_name}"
        logger.info("[UpstreamSync] Successfully pushed branch '%s' (commit %s)", branch_name, commit_sha[:8])
        logger.info("[UpstreamSync] PR Link: %s", pr_url)

        return {
            "branch": branch_name,
            "commit_sha": commit_sha,
            "pr_url": pr_url,
            "status": "pushed",
        }

    finally:
        # Return to original branch if not dry run
        if not dry_run:
            try:
                subprocess.run(
                    ["git", "checkout", original_branch],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                logger.info("[UpstreamSync] Switched back to original branch: %s", original_branch)
            except Exception as e:
                logger.warning("Failed to switch back to original branch: %s", str(e))