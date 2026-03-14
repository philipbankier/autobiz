"""
Git service for company code repositories.
Async wrappers around git CLI for commit, push, and status operations.
"""
import asyncio
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")


def _code_dir(slug: str) -> Path:
    return COMPANIES_DIR / slug / "code"


def _auth_clone_url(clone_url: str) -> str:
    """Embed PAT into clone URL for auth: https://{PAT}@github.com/..."""
    pat = settings.GITHUB_PAT
    if not pat:
        raise RuntimeError("GITHUB_PAT not configured")
    return clone_url.replace("https://", f"https://{pat}@")


def _read_env(slug: str) -> dict[str, str]:
    """Read key=value pairs from companies/{slug}/.env."""
    env_file = COMPANIES_DIR / slug / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


async def _run_git(slug: str, *args: str) -> tuple[int, str, str]:
    """Run a git command in the company's code directory."""
    cwd = _code_dir(slug)
    if not cwd.exists():
        cwd.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        "git", *args,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode().strip(), stderr.decode().strip()


async def git_init(slug: str) -> dict:
    """Initialize a git repo in companies/{slug}/code/ if not already."""
    cwd = _code_dir(slug)
    if (cwd / ".git").exists():
        return {"status": "already_initialized"}

    cwd.mkdir(parents=True, exist_ok=True)
    rc, out, err = await _run_git(slug, "init")
    if rc != 0:
        return {"status": "error", "message": err}

    # Configure git user for commits
    await _run_git(slug, "config", "user.email", "agent@autobiz.app")
    await _run_git(slug, "config", "user.name", "AutoBiz Agent")

    return {"status": "initialized"}


async def git_setup_remote(slug: str, clone_url: str | None = None) -> dict:
    """Configure remote 'origin' with PAT auth."""
    if not clone_url:
        env = _read_env(slug)
        clone_url = env.get("GITHUB_CLONE_URL")
        if not clone_url:
            return {"status": "error", "message": "No GITHUB_CLONE_URL in .env"}

    auth_url = _auth_clone_url(clone_url)

    # Check if remote exists
    rc, out, _ = await _run_git(slug, "remote", "get-url", "origin")
    if rc == 0:
        # Update existing remote
        await _run_git(slug, "remote", "set-url", "origin", auth_url)
        return {"status": "updated", "remote": "origin"}
    else:
        # Add new remote
        rc, out, err = await _run_git(slug, "remote", "add", "origin", auth_url)
        if rc != 0:
            return {"status": "error", "message": err}
        return {"status": "added", "remote": "origin"}


async def git_commit(slug: str, message: str) -> dict:
    """Stage all changes and commit."""
    # Ensure repo is initialized
    await git_init(slug)

    # Stage all
    rc, out, err = await _run_git(slug, "add", "-A")
    if rc != 0:
        return {"status": "error", "message": f"git add failed: {err}"}

    # Check if there's anything to commit
    rc, out, _ = await _run_git(slug, "diff", "--cached", "--quiet")
    if rc == 0:
        return {"status": "no_changes", "message": "Nothing to commit"}

    # Commit
    rc, out, err = await _run_git(slug, "commit", "-m", message)
    if rc != 0:
        return {"status": "error", "message": f"git commit failed: {err}"}

    # Get commit hash
    rc2, sha, _ = await _run_git(slug, "rev-parse", "--short", "HEAD")
    return {"status": "committed", "message": message, "sha": sha}


async def git_push(slug: str) -> dict:
    """Push to origin. Sets up remote with PAT auth if needed."""
    # Ensure remote is configured with auth
    remote_result = await git_setup_remote(slug)
    if remote_result.get("status") == "error":
        return remote_result

    # Determine current branch
    rc, branch, _ = await _run_git(slug, "rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0:
        branch = "main"

    # Push
    rc, out, err = await _run_git(slug, "push", "-u", "origin", branch)
    if rc != 0:
        # If remote is empty, try setting upstream
        if "has no upstream" in err or "src refspec" in err:
            rc, out, err = await _run_git(slug, "push", "--set-upstream", "origin", branch)
        if rc != 0:
            return {"status": "error", "message": f"git push failed: {err}"}

    return {"status": "pushed", "branch": branch}


async def git_status(slug: str) -> dict:
    """Check for uncommitted changes."""
    cwd = _code_dir(slug)
    if not (cwd / ".git").exists():
        return {"status": "not_initialized"}

    rc, out, _ = await _run_git(slug, "status", "--porcelain")
    has_changes = bool(out.strip())

    # Get current branch and last commit
    _, branch, _ = await _run_git(slug, "rev-parse", "--abbrev-ref", "HEAD")
    _, last_commit, _ = await _run_git(slug, "log", "--oneline", "-1")

    return {
        "status": "clean" if not has_changes else "dirty",
        "has_changes": has_changes,
        "changed_files": out.strip().splitlines() if has_changes else [],
        "branch": branch,
        "last_commit": last_commit,
    }
