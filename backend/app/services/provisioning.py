"""
Company provisioning service.
When a user creates a company, this service sets up all the real infrastructure:
- Workspace (files, memory, knowledge graph)
- GitHub repo
- Vercel project (auto-deploy from GitHub)
- Stripe Connect sub-account
- Resend email subdomain
Each company gets isolated resources. Agents work within these boundaries.
"""
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")
GITHUB_ORG = "autobiz-companies"  # or user's own account


class ProvisioningError(Exception):
    """Raised when provisioning a resource fails."""
    pass


class CompanyProvisioner:
    """Provisions all infrastructure for a new company."""

    def __init__(self, company_id: str, slug: str, name: str, mission: str = ""):
        self.company_id = company_id
        self.slug = slug
        self.name = name
        self.mission = mission
        self.workspace = COMPANIES_DIR / slug
        self.results: dict = {}

    async def provision_all(self) -> dict:
        """
        Run all provisioning steps. Each step is independent and logs its own
        success/failure. Returns a summary of what was provisioned.
        """
        steps = [
            ("workspace", self.provision_workspace),
            ("github", self.provision_github),
            ("vercel", self.provision_vercel),
            ("stripe", self.provision_stripe),
            ("email", self.provision_email),
            ("scheduler", self.provision_scheduler),
        ]

        for step_name, step_fn in steps:
            try:
                result = await step_fn()
                self.results[step_name] = {"status": "ok", **result}
                logger.info(f"[{self.slug}] Provisioned {step_name}: {result}")
            except Exception as e:
                self.results[step_name] = {"status": "error", "message": str(e)}
                logger.error(f"[{self.slug}] Failed to provision {step_name}: {e}")

        return self.results

    async def provision_workspace(self) -> dict:
        """Create the company workspace directory structure."""
        # Core dirs
        dirs = [
            self.workspace,
            self.workspace / "code",
            self.workspace / "content",
            self.workspace / "site",
            self.workspace / "knowledge",
            self.workspace / "skills",
        ]
        # Department dirs with ralph loop structure
        for dept in ["ceo", "developer", "marketing", "sales", "finance", "support"]:
            dirs.append(self.workspace / "departments" / dept)

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # Department PLAN.md and MEMORY.md files
        for dept in ["ceo", "developer", "marketing", "sales", "finance", "support"]:
            dept_dir = self.workspace / "departments" / dept
            plan_md = dept_dir / "PLAN.md"
            if not plan_md.exists():
                plan_md.write_text(f"# {dept.upper()} — Task Plan\n\n## Tasks\n\n(No tasks yet — CEO will create the initial plan)\n")
            dept_memory = dept_dir / "MEMORY.md"
            if not dept_memory.exists():
                dept_memory.write_text(f"# {dept.upper()} — Department Memory\n\n## Key Decisions\n\n## Lessons Learned\n\n## Important Context\n")

        # STEERING.md — human can edit anytime to redirect agents
        steering_md = self.workspace / "STEERING.md"
        if not steering_md.exists():
            steering_md.write_text(f"""# Steering — Human Overrides

Edit this file anytime to redirect the agents. They check it at the start of each run.

## Current Direction
(No overrides — agents operating autonomously)

## Priority Override
(Leave empty unless you want to force a specific focus)

## Blocked Actions
(List anything agents should NOT do right now)
""")

        # COMPANY.md — the company's "brain"
        company_md = self.workspace / "COMPANY.md"
        if not company_md.exists():
            company_md.write_text(f"""# {self.name}

## ID
{self.company_id}

## Slug
{self.slug}

## Mission
{self.mission or "(To be defined by CEO agent)"}

## Current Stage
planning

## Business Model
(To be determined)

## Target Audience
(To be determined)

## Key Metrics
- Revenue: $0
- Users: 0
- MRR: $0

## Strategy
(CEO agent will develop this)
""")

        # MEMORY.md — persistent agent memory
        memory_md = self.workspace / "MEMORY.md"
        if not memory_md.exists():
            memory_md.write_text(f"""# {self.slug} — Agent Memory

## Key Decisions

## Lessons Learned

## Important Context

## Action Log
""")

        # Knowledge graph
        kg_file = self.workspace / "knowledge" / "graph.jsonl"
        if not kg_file.exists():
            kg_file.write_text("")

        # .env for company-specific secrets (populated later)
        env_file = self.workspace / ".env"
        if not env_file.exists():
            env_file.write_text(f"# {self.slug} — Company Environment\n# Populated during provisioning\n")

        return {"path": str(self.workspace), "dirs": [d.name for d in dirs]}

    async def provision_github(self) -> dict:
        """Create a GitHub repo for the company's product code."""
        github_pat = settings.GITHUB_PAT
        if not github_pat:
            raise ProvisioningError("GITHUB_PAT not configured")

        repo_name = f"autobiz-{self.slug}"
        
        # Create repo via GitHub API
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {github_pat}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "name": repo_name,
                    "description": f"AutoBiz company: {self.name}",
                    "private": True,
                    "auto_init": True,
                },
                timeout=15.0,
            )

            if resp.status_code == 422:
                # Repo might already exist
                data = resp.json()
                if any("already exists" in str(e) for e in data.get("errors", [])):
                    return {"repo": repo_name, "note": "already exists"}
                raise ProvisioningError(f"GitHub API error: {data}")
            
            if resp.status_code not in (200, 201):
                raise ProvisioningError(f"GitHub API {resp.status_code}: {resp.text}")

            repo_data = resp.json()

        # Init local git in company code directory
        code_dir = self.workspace / "code"
        if not (code_dir / ".git").exists():
            subprocess.run(["git", "init"], cwd=code_dir, capture_output=True)
            subprocess.run(
                ["git", "remote", "add", "origin", repo_data["clone_url"]],
                cwd=code_dir, capture_output=True,
            )

        # Store repo info in company .env
        env_file = self.workspace / ".env"
        with open(env_file, "a") as f:
            f.write(f"\nGITHUB_REPO={repo_data['full_name']}\n")
            f.write(f"GITHUB_CLONE_URL={repo_data['clone_url']}\n")

        return {
            "repo": repo_data["full_name"],
            "url": repo_data["html_url"],
            "clone_url": repo_data["clone_url"],
        }

    async def provision_vercel(self) -> dict:
        """Create a Vercel project linked to the GitHub repo."""
        vercel_token = settings.VERCEL_TOKEN
        if not vercel_token:
            raise ProvisioningError("VERCEL_TOKEN not configured")

        project_name = f"autobiz-{self.slug}"
        github_repo = self.results.get("github", {}).get("repo")

        async with httpx.AsyncClient() as client:
            # Create project
            create_payload = {
                "name": project_name,
                "framework": None,  # Static or auto-detect
            }

            # If GitHub repo was created, link it
            if github_repo:
                create_payload["gitRepository"] = {
                    "type": "github",
                    "repo": github_repo,
                }

            resp = await client.post(
                "https://api.vercel.com/v10/projects",
                headers={
                    "Authorization": f"Bearer {vercel_token}",
                    "Content-Type": "application/json",
                },
                json=create_payload,
                timeout=15.0,
            )

            if resp.status_code == 409:
                return {"project": project_name, "note": "already exists"}

            if resp.status_code not in (200, 201):
                raise ProvisioningError(f"Vercel API {resp.status_code}: {resp.text[:200]}")

            project_data = resp.json()

        # Store project info
        env_file = self.workspace / ".env"
        with open(env_file, "a") as f:
            f.write(f"\nVERCEL_PROJECT_ID={project_data.get('id', '')}\n")
            f.write(f"VERCEL_PROJECT_NAME={project_name}\n")

        return {
            "project": project_name,
            "project_id": project_data.get("id"),
            "url": f"https://{project_name}.vercel.app",
        }

    async def provision_stripe(self) -> dict:
        """Create a Stripe Connect Express account for the company."""
        stripe_key = settings.STRIPE_SECRET_KEY
        if not stripe_key:
            raise ProvisioningError("STRIPE_SECRET_KEY not configured")

        async with httpx.AsyncClient() as client:
            # Create a Connected Account (Express)
            resp = await client.post(
                "https://api.stripe.com/v1/accounts",
                auth=(stripe_key, ""),
                data={
                    "type": "express",
                    "country": "US",
                    "email": f"{self.slug}@autobiz.app",
                    "capabilities[card_payments][requested]": "true",
                    "capabilities[transfers][requested]": "true",
                    "business_profile[name]": self.name,
                    "metadata[autobiz_company_id]": self.company_id,
                    "metadata[autobiz_slug]": self.slug,
                },
                timeout=15.0,
            )

            if resp.status_code not in (200, 201):
                raise ProvisioningError(f"Stripe API {resp.status_code}: {resp.text[:200]}")

            account_data = resp.json()

            # Create onboarding link for the user to complete Stripe setup
            onboard_resp = await client.post(
                "https://api.stripe.com/v1/account_links",
                auth=(stripe_key, ""),
                data={
                    "account": account_data["id"],
                    "refresh_url": f"https://autobiz.app/companies/{self.slug}/stripe/refresh",
                    "return_url": f"https://autobiz.app/companies/{self.slug}/stripe/complete",
                    "type": "account_onboarding",
                },
                timeout=15.0,
            )

            onboard_url = ""
            if onboard_resp.status_code in (200, 201):
                onboard_url = onboard_resp.json().get("url", "")

        # Store Stripe account info
        env_file = self.workspace / ".env"
        with open(env_file, "a") as f:
            f.write(f"\nSTRIPE_CONNECT_ACCOUNT_ID={account_data['id']}\n")

        return {
            "account_id": account_data["id"],
            "onboarding_url": onboard_url,
        }

    async def provision_scheduler(self) -> dict:
        """Register OpenClaw cron jobs for automated department cycles."""
        from app.services.scheduler import register_company_cron_jobs

        results = await register_company_cron_jobs(self.company_id, self.slug)
        registered = sum(1 for r in results.values() if r.get("status") == "registered")
        total = len(results)

        if registered == 0:
            raise ProvisioningError(f"No cron jobs registered (0/{total})")

        return {
            "registered": registered,
            "total": total,
            "jobs": results,
        }

    async def provision_email(self) -> dict:
        """Set up email sending via Resend for this company."""
        resend_key = settings.RESEND_API_KEY
        if not resend_key:
            raise ProvisioningError("RESEND_API_KEY not configured")

        # For now, companies share the platform's Resend account
        # and send from {slug}@autobiz.app (once domain is verified)
        # Later: per-company domains
        
        from_email = f"{self.slug}@autobiz.app"
        
        # Store email config
        env_file = self.workspace / ".env"
        with open(env_file, "a") as f:
            f.write(f"\nEMAIL_FROM={from_email}\n")
            f.write(f"RESEND_API_KEY={resend_key}\n")

        return {
            "from_email": from_email,
            "provider": "resend",
            "note": "Domain autobiz.app must be verified in Resend for production use",
        }


async def provision_company(
    company_id: str,
    slug: str,
    name: str,
    mission: str = "",
) -> dict:
    """Top-level function to provision all infrastructure for a company."""
    provisioner = CompanyProvisioner(company_id, slug, name, mission)
    results = await provisioner.provision_all()

    # Summary
    ok_count = sum(1 for r in results.values() if r.get("status") == "ok")
    total = len(results)
    
    return {
        "summary": f"{ok_count}/{total} services provisioned",
        "company_id": company_id,
        "slug": slug,
        "workspace": str(provisioner.workspace),
        "services": results,
    }
