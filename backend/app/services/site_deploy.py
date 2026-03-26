"""
Site deployment service.
Manages generated business websites — local file serving + Vercel deployment via git.
Flow: copy site/ files into code/ → git commit → git push → Vercel auto-deploys.
"""
import logging
import os
import shutil
from pathlib import Path

import httpx

from app.config import settings
from app.services.git_service import git_commit, git_push, git_status, git_init, _read_env

logger = logging.getLogger(__name__)

COMPANIES_DIR = Path(os.environ.get("COMPANIES_DIR", "/app/companies"))
SITES_DIR = Path(os.environ.get("SITES_DIR", "/app/sites"))  # Served by nginx/caddy


def get_site_dir(company_slug: str) -> Path:
    """Get the site directory for a company."""
    site_dir = SITES_DIR / company_slug
    site_dir.mkdir(parents=True, exist_ok=True)
    return site_dir


def get_site_url(company_slug: str) -> str:
    """Get the public URL for a company site."""
    return f"https://{company_slug}.{settings.SITE_BASE_DOMAIN}"


def copy_site_to_code(company_slug: str) -> list[str]:
    """Copy site/ files into code/ directory for git deployment."""
    workspace = COMPANIES_DIR / company_slug
    site_subdir = workspace / "site"
    code_dir = workspace / "code"

    if not site_subdir.exists():
        return []

    code_dir.mkdir(parents=True, exist_ok=True)
    copied = []

    for src_file in site_subdir.rglob("*"):
        if src_file.is_file():
            rel = src_file.relative_to(site_subdir)
            dest = code_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest)
            copied.append(str(rel))

    # Ensure index.html exists
    landing = code_dir / "landing-page.html"
    index = code_dir / "index.html"
    if landing.exists() and not index.exists():
        shutil.copy2(landing, index)
        copied.append("index.html (from landing-page.html)")

    return copied


def deploy_site(company_slug: str) -> dict:
    """
    Deploy the company's site from workspace to local serving directory.
    Looks for HTML/static files in the company workspace and copies to sites dir.
    """
    workspace = COMPANIES_DIR / company_slug
    site_dir = get_site_dir(company_slug)

    if not workspace.exists():
        return {"status": "error", "message": "Company workspace not found"}

    # Find deployable files
    deployed_files = []
    for ext in ["*.html", "*.css", "*.js", "*.json", "*.svg", "*.png", "*.jpg", "*.ico"]:
        for src_file in workspace.glob(ext):
            dest = site_dir / src_file.name
            shutil.copy2(src_file, dest)
            deployed_files.append(src_file.name)

    # Also check for site/ subdirectory
    site_subdir = workspace / "site"
    if site_subdir.exists():
        for src_file in site_subdir.rglob("*"):
            if src_file.is_file():
                rel = src_file.relative_to(site_subdir)
                dest = site_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)
                deployed_files.append(str(rel))

    # If there's a landing-page.html but no index.html, rename it
    landing = site_dir / "landing-page.html"
    index = site_dir / "index.html"
    if landing.exists() and not index.exists():
        shutil.copy2(landing, index)
        deployed_files.append("index.html (from landing-page.html)")

    if not deployed_files:
        return {
            "status": "empty",
            "message": "No deployable files found in workspace",
            "url": get_site_url(company_slug),
        }

    logger.info(f"Deployed {len(deployed_files)} files for {company_slug}")

    return {
        "status": "deployed",
        "url": get_site_url(company_slug),
        "files": deployed_files,
        "local_path": str(site_dir),
    }


def get_site_status(company_slug: str) -> dict:
    """Check the deployment status of a company site."""
    site_dir = SITES_DIR / company_slug

    if not site_dir.exists():
        return {"status": "not_deployed", "url": get_site_url(company_slug)}

    files = list(site_dir.rglob("*"))
    file_count = sum(1 for f in files if f.is_file())
    has_index = (site_dir / "index.html").exists()

    return {
        "status": "deployed" if has_index else "partial",
        "url": get_site_url(company_slug),
        "file_count": file_count,
        "has_index": has_index,
        "local_path": str(site_dir),
    }


async def deploy_to_vercel(company_slug: str) -> dict:
    """
    Full deploy pipeline: copy site/ → code/, git commit, git push.
    Vercel auto-deploys from the linked GitHub repo.
    """
    # 1. Copy site files into code/
    copied = copy_site_to_code(company_slug)
    if copied:
        logger.info(f"[{company_slug}] Copied {len(copied)} site files to code/")

    # 2. Git commit
    commit_result = await git_commit(company_slug, f"deploy: update site ({len(copied)} files)")
    if commit_result["status"] == "error":
        return {"status": "error", "step": "commit", **commit_result}

    if commit_result["status"] == "no_changes":
        return {"status": "no_changes", "message": "No changes to deploy"}

    # 3. Git push → triggers Vercel auto-deploy
    push_result = await git_push(company_slug)
    if push_result["status"] == "error":
        return {"status": "error", "step": "push", **push_result}

    # 4. Get deploy URL
    env = _read_env(company_slug)
    vercel_project = env.get("VERCEL_PROJECT_NAME", f"autobiz-{company_slug}")

    return {
        "status": "deployed",
        "commit": commit_result.get("sha"),
        "branch": push_result.get("branch"),
        "files_copied": len(copied),
        "vercel_url": f"https://{vercel_project}.vercel.app",
        "site_url": get_site_url(company_slug),
    }


async def check_deploy_status(company_slug: str) -> dict:
    """Check latest Vercel deployment status via API."""
    vercel_token = settings.VERCEL_TOKEN
    if not vercel_token:
        return {"status": "error", "message": "VERCEL_TOKEN not configured"}

    env = _read_env(company_slug)
    project_id = env.get("VERCEL_PROJECT_ID")
    if not project_id:
        return {"status": "error", "message": "No VERCEL_PROJECT_ID in company .env"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.vercel.com/v6/deployments",
            params={"projectId": project_id, "limit": 5},
            headers={"Authorization": f"Bearer {vercel_token}"},
            timeout=10.0,
        )

        if resp.status_code != 200:
            return {"status": "error", "message": f"Vercel API {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        deployments = data.get("deployments", [])

    if not deployments:
        return {"status": "no_deployments", "deployments": []}

    return {
        "status": "ok",
        "latest": {
            "state": deployments[0].get("state"),
            "url": deployments[0].get("url"),
            "created": deployments[0].get("created"),
        },
        "deployments": [
            {
                "uid": d.get("uid"),
                "state": d.get("state"),
                "url": d.get("url"),
                "created": d.get("created"),
            }
            for d in deployments
        ],
    }


async def get_deploy_url(company_slug: str) -> dict:
    """Get the live Vercel URL for the company."""
    env = _read_env(company_slug)
    vercel_project = env.get("VERCEL_PROJECT_NAME", f"autobiz-{company_slug}")
    return {
        "vercel_url": f"https://{vercel_project}.vercel.app",
        "site_url": get_site_url(company_slug),
    }
