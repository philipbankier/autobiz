"""
OpenClaw Gateway integration service.
Spawns agent sessions via the Gateway HTTP API (/tools/invoke).
Agents get full OpenClaw capabilities: exec, file access, MCP tools, memory, web search, etc.
"""
import json
import logging
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GATEWAY_URL = "http://127.0.0.1:18789"
COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")

# Map AutoBiz department types to OpenClaw agent IDs
DEPT_TO_AGENT = {
    "ceo": "orchestrator",
    "developer": "developer",
    "marketing": "marketing",
    "sales": "marketing",       # Shares marketing agent, sales-specific via task
    "finance": "researcher",    # Uses researcher for analysis
    "support": "coordinator",   # Uses coordinator for monitoring/support
}


def _get_gateway_token() -> str:
    """Read gateway auth token from OpenClaw config."""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config["gateway"]["auth"]["token"]
    except (FileNotFoundError, KeyError) as e:
        logger.error(f"Cannot read gateway token: {e}")
        return settings.OPENCLAW_GATEWAY_TOKEN if hasattr(settings, 'OPENCLAW_GATEWAY_TOKEN') else ""


def get_company_workspace(company_id: str, slug: str) -> Path:
    """Get or create workspace directory for a company."""
    workspace = COMPANIES_DIR / slug
    workspace.mkdir(parents=True, exist_ok=True)

    # Ensure essential files exist
    company_md = workspace / "COMPANY.md"
    if not company_md.exists():
        company_md.write_text(f"# Company: {slug}\nID: {company_id}\n\n## Mission\n(Not yet defined)\n\n## Current Stage\nPlanning\n")

    memory_md = workspace / "MEMORY.md"
    if not memory_md.exists():
        memory_md.write_text(f"# {slug} — Agent Memory\n\n## Key Decisions\n\n## Lessons Learned\n\n## Important Context\n")

    kg_dir = workspace / "knowledge"
    kg_dir.mkdir(exist_ok=True)
    kg_file = kg_dir / "graph.jsonl"
    if not kg_file.exists():
        kg_file.write_text("")

    (workspace / "code").mkdir(exist_ok=True)
    (workspace / "content").mkdir(exist_ok=True)
    (workspace / "site").mkdir(exist_ok=True)

    return workspace


def _build_task_prompt(
    company_name: str,
    company_mission: str,
    department_type: str,
    task_description: str,
    pending_tasks: list[dict] | None = None,
    chat_history: list[dict] | None = None,
) -> str:
    """Build the task prompt for an agent session."""
    
    tasks_section = ""
    if pending_tasks:
        tasks_section = "\n## Your Pending Tasks\n"
        for t in pending_tasks:
            tasks_section += f"- [{t['priority']}] {t['title']}: {t['description']}\n"

    chat_section = ""
    if chat_history:
        chat_section = "\n## Recent Messages from the Human Owner\n"
        for msg in chat_history[-5:]:
            chat_section += f"- {msg['role']}: {msg['content']}\n"

    role_desc = _get_role_description(department_type)

    return f"""You are the {department_type.upper()} department of "{company_name}".

## Company Mission
{company_mission}

## Your Role
{role_desc}

## Workspace
You are working in the company workspace. Key files:
- COMPANY.md — Company context and strategy (read this first, update if you make strategic decisions)
- MEMORY.md — Persistent memory across runs (update with important learnings)
- knowledge/graph.jsonl — Knowledge graph (append new entities as JSONL)
- code/ — Product source code
- content/ — Marketing content (blog posts, social media drafts)
- site/ — Built/deployable website assets
{tasks_section}{chat_section}
## Your Task
{task_description}

## Instructions
1. Read COMPANY.md first for context
2. Execute your task using the tools available to you
3. Update MEMORY.md with anything important you learned or decided
4. If you create/modify files, note what you changed
5. Be concise in your final summary
"""


def _get_role_description(department_type: str) -> str:
    """Department-specific role descriptions."""
    roles = {
        "ceo": """You are the CEO. You set strategic direction, review progress, create and prioritize tasks 
for other departments, and make key business decisions. Update COMPANY.md with strategy changes.""",
        
        "developer": """You are the lead developer. You write production-quality code, build features, 
fix bugs, run tests, and handle deployments. Work in the code/ directory. Use git for version control.
Run builds with npm/node to verify your work compiles.""",
        
        "marketing": """You are the marketing director. You create compelling content (blog posts, social media 
posts, email copy), plan campaigns, and track engagement. Save content drafts to content/. 
Research competitors and trending topics.""",
        
        "sales": """You are the sales lead. You optimize conversion funnels, create landing page copy, 
set up pricing, and track sales metrics. Focus on what drives signups and revenue.""",
        
        "finance": """You are the CFO. You track revenue, costs, and profitability. Create financial 
reports and projections. Monitor agent spending and ROI. Recommend budget adjustments.""",
        
        "support": """You are the support lead. You monitor customer inquiries, create FAQ documentation, 
triage issues, and ensure customer satisfaction. Document common issues and solutions.""",
    }
    return roles.get(department_type, "Execute your assigned tasks efficiently.")


async def spawn_agent_session(
    company_id: str,
    company_slug: str,
    company_name: str,
    company_mission: str,
    department_type: str,
    task_description: str,
    pending_tasks: list[dict] | None = None,
    chat_history: list[dict] | None = None,
    timeout_seconds: int = 300,
    model: str | None = None,
) -> dict:
    """
    Spawn an OpenClaw agent session via the Gateway HTTP API.
    Returns immediately with session info. Results come async via announce.
    """
    workspace = get_company_workspace(company_id, company_slug)
    agent_id = DEPT_TO_AGENT.get(department_type, "coordinator")
    token = _get_gateway_token()

    if not token:
        return {"status": "error", "message": "No gateway token configured"}

    task_prompt = _build_task_prompt(
        company_name=company_name,
        company_mission=company_mission,
        department_type=department_type,
        task_description=task_description,
        pending_tasks=pending_tasks,
        chat_history=chat_history,
    )

    spawn_args: dict = {
        "agentId": agent_id,
        "task": task_prompt,
        "cwd": str(workspace),
        "mode": "run",
        "runTimeoutSeconds": timeout_seconds,
    }
    if model:
        spawn_args["model"] = model

    logger.info(f"Spawning {department_type} agent (openclaw:{agent_id}) for {company_slug}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/tools/invoke",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "tool": "sessions_spawn",
                    "args": spawn_args,
                },
                timeout=30.0,  # Just the spawn request, not the run
            )
            
            result = response.json()

            if not result.get("ok"):
                error = result.get("error", {})
                logger.error(f"Gateway spawn failed: {error}")
                return {
                    "status": "error",
                    "message": error.get("message", str(error)),
                }

            details = result.get("result", {}).get("details", {})
            return {
                "status": "accepted",
                "session_key": details.get("childSessionKey"),
                "run_id": details.get("runId"),
                "agent_id": agent_id,
                "department": department_type,
                "company_slug": company_slug,
            }

    except httpx.TimeoutException:
        logger.error(f"Gateway timeout for {department_type}/{company_slug}")
        return {"status": "error", "message": "Gateway request timed out"}
    except Exception as e:
        logger.error(f"Gateway error: {e}")
        return {"status": "error", "message": str(e)}


async def send_to_session(session_key: str, message: str) -> dict:
    """Send a message to an existing agent session."""
    token = _get_gateway_token()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/tools/invoke",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "tool": "sessions_send",
                    "args": {
                        "sessionKey": session_key,
                        "message": message,
                    },
                },
                timeout=30.0,
            )
            return response.json()
    except Exception as e:
        return {"ok": False, "error": {"message": str(e)}}


async def list_active_sessions() -> dict:
    """List active agent sessions from the gateway."""
    token = _get_gateway_token()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/tools/invoke",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "tool": "sessions_list",
                    "args": {"limit": 20, "kinds": ["subagent"]},
                },
                timeout=10.0,
            )
            return response.json()
    except Exception as e:
        return {"ok": False, "error": {"message": str(e)}}
