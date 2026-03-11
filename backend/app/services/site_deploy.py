"""
Site deployment service.
Manages generated business websites — builds and deploys them.
Phase 3: local file serving. Phase 5: Vercel/Cloudflare deployment.
"""
import logging
import shutil
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")
SITES_DIR = Path("/home/philip/TinkerLab/autobiz/sites")  # Served by nginx/caddy


def get_site_dir(company_slug: str) -> Path:
    """Get the site directory for a company."""
    site_dir = SITES_DIR / company_slug
    site_dir.mkdir(parents=True, exist_ok=True)
    return site_dir


def get_site_url(company_slug: str) -> str:
    """Get the public URL for a company site."""
    return f"https://{company_slug}.{settings.SITE_BASE_DOMAIN}"


def deploy_site(company_slug: str) -> dict:
    """
    Deploy the company's site from workspace to serving directory.
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
