"""
OpenClaw Gateway integration service.
Spawns agent sessions via the Gateway HTTP API (/tools/invoke).

Implements:
- Ralph loop pattern (fresh context per iteration, PLAN.md-driven)
- Budget enforcement (check before run, kill on exceed)
- Model tiering (Opus for CEO, Sonnet for execution, Haiku for judging)
- STEERING.md human override support
- Post-run memory consolidation
"""
import json
import logging
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.services.cost_control import (
    get_model_for_department,
    JUDGE_MODEL,
)

logger = logging.getLogger(__name__)

import os as _os
GATEWAY_URL = _os.environ.get("OPENCLAW_GATEWAY_URL", "http://host.docker.internal:18789")
COMPANIES_DIR = Path(_os.environ.get("COMPANIES_DIR", "/app/companies"))

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
        return ""


def get_company_workspace(company_id: str, slug: str) -> Path:
    """Get workspace directory for a company."""
    return COMPANIES_DIR / slug


def _read_file_safe(path: Path, max_chars: int = 2000) -> str:
    """Read a file safely, returning empty string if missing."""
    try:
        text = path.read_text()
        return text[:max_chars] if len(text) > max_chars else text
    except FileNotFoundError:
        return ""


def _get_steering(workspace: Path) -> str:
    """Read STEERING.md for human overrides."""
    content = _read_file_safe(workspace / "STEERING.md")
    if not content or "No overrides" in content:
        return ""
    return f"\n## Human Steering (PRIORITY — follow these instructions)\n{content}\n"


def _get_department_plan(workspace: Path, department_type: str) -> str:
    """Read the department's PLAN.md for current tasks."""
    plan_path = workspace / "departments" / department_type / "PLAN.md"
    content = _read_file_safe(plan_path, max_chars=3000)
    if not content:
        return ""
    return f"\n## Your Current Plan\n{content}\n"


def _get_department_memory(workspace: Path, department_type: str) -> str:
    """Read the department's memory file."""
    memory_path = workspace / "departments" / department_type / "MEMORY.md"
    content = _read_file_safe(memory_path, max_chars=2000)
    if not content:
        return ""
    return f"\n## Your Memory (from previous runs)\n{content}\n"


def _get_role_description(department_type: str) -> str:
    """Department-specific role descriptions with ralph loop instructions."""
    roles = {
        "ceo": """You are the CEO. You set strategic direction, review progress, create and prioritize tasks 
for other departments, and make key business decisions.

Your primary output is updating:
- COMPANY.md — with strategy, business model, target audience
- departments/*/PLAN.md — with specific tasks for each department (use checkbox format: - [ ] task)
- Your own departments/ceo/PLAN.md — with your strategic tasks

When creating tasks for departments, use this format in their PLAN.md:
- [ ] Task title: Detailed description of what to do and what success looks like
""",
        
        "developer": """You are the lead developer. You write production-quality code, build features, 
fix bugs, run tests, and handle deployments. Work in the code/ directory.

Ralph Loop Rules:
1. Read departments/developer/PLAN.md to find the next unchecked task (- [ ])
2. Execute ONLY that one task
3. Validate your work (run tests, check for errors)
4. If valid: mark it done (- [x]) and git commit
5. Update departments/developer/MEMORY.md with what you learned
6. DO NOT work on multiple tasks in one run
""",
        
        "marketing": """You are the marketing director. You create compelling content (blog posts, social media
posts, email copy), plan campaigns, and track engagement.

## Social Media Integration
You can queue social media posts for automatic publishing:
- Write tweets to content/tweets.json as: [{"text": "...", "status": "pending"}]
- Write LinkedIn posts to content/linkedin.json as: [{"text": "...", "status": "pending"}]
- After your run completes, pending items are automatically posted via the Twitter and LinkedIn APIs.
- Keep tweets under 280 characters.
- Include relevant hashtags and compelling CTAs.
- Schedule content by adding "publish_at" (ISO datetime) to entries.

## Email Campaigns
You can queue marketing emails:
- Write to content/emails.json as: [{"to": "...", "subject": "...", "html_body": "...", "status": "pending"}]
- Pending emails are sent automatically after your run via Resend.
- From address is {company_slug}@autobiz.app.

Ralph Loop Rules:
1. Read departments/marketing/PLAN.md to find the next unchecked task
2. Execute ONLY that one task
3. Save content drafts to content/ — use tweets.json and emails.json for auto-dispatch
4. Mark task done and update your memory
5. DO NOT work on multiple tasks in one run
""",
        
        "sales": """You are the sales lead. You optimize conversion funnels, create landing page copy,
set up pricing, and track sales metrics.

## Email Outreach
You can queue outreach emails for automatic sending:
- Write to content/emails.json as: [{"to": "user@example.com", "subject": "...", "html_body": "...", "status": "pending"}]
- Pending emails are sent automatically after your run via Resend.
- From address is {company_slug}@autobiz.app.
- Max 10 emails per batch. Focus on high-quality, personalized outreach.

Ralph Loop Rules:
1. Read departments/sales/PLAN.md to find the next unchecked task
2. Execute ONLY that one task
3. Mark task done and update your memory
""",
        
        "finance": """You are the CFO. You track revenue, costs, and profitability. Create financial 
reports and projections. Monitor agent spending and ROI.

Ralph Loop Rules:
1. Read departments/finance/PLAN.md to find the next unchecked task
2. Execute ONLY that one task
3. Mark task done and update your memory
""",
        
        "support": """You are the support lead. You monitor customer inquiries, create FAQ documentation,
triage issues, and ensure customer satisfaction.

## Support Emails
You can queue support response emails:
- Write to content/emails.json as: [{"to": "customer@example.com", "subject": "...", "html_body": "...", "status": "pending"}]
- Pending emails are sent automatically after your run via Resend.
- From address is {company_slug}@autobiz.app.
- Always be helpful, professional, and empathetic in support emails.

Ralph Loop Rules:
1. Read departments/support/PLAN.md to find the next unchecked task
2. Execute ONLY that one task
3. Mark task done and update your memory
""",
    }
    return roles.get(department_type, "Execute your assigned tasks efficiently.")


def _build_task_prompt(
    company_name: str,
    company_mission: str,
    department_type: str,
    task_description: str,
    workspace: Path,
    pending_tasks: list[dict] | None = None,
    chat_history: list[dict] | None = None,
) -> str:
    """Build the task prompt for an agent session with ralph loop structure."""
    
    # Read company context
    company_context = _read_file_safe(workspace / "COMPANY.md", max_chars=2000)
    
    # Read human steering overrides
    steering = _get_steering(workspace)
    
    # Read department plan and memory
    plan = _get_department_plan(workspace, department_type)
    memory = _get_department_memory(workspace, department_type)

    # Legacy pending tasks (from DB)
    tasks_section = ""
    if pending_tasks:
        tasks_section = "\n## Additional Pending Tasks (from queue)\n"
        for t in pending_tasks:
            tasks_section += f"- [{t['priority']}] {t['title']}: {t['description']}\n"

    chat_section = ""
    if chat_history:
        chat_section = "\n## Recent Messages from the Human Owner\n"
        for msg in chat_history[-5:]:
            chat_section += f"- {msg['role']}: {msg['content']}\n"

    role_desc = _get_role_description(department_type)

    abs_workspace = str(workspace.resolve())

    return f"""You are the {department_type.upper()} department of "{company_name}".

## Company Mission
{company_mission}

## Your Role
{role_desc}
{steering}
## Company Context
{company_context}
{plan}{memory}
## IMPORTANT: Company Workspace Location
All company files are at: {abs_workspace}
You MUST read and write files using this absolute path. Do NOT create files in your default workspace.

Key files (use absolute paths):
- {abs_workspace}/COMPANY.md — Company strategy (read first, CEO updates this)
- {abs_workspace}/STEERING.md — Human overrides (check for instructions)
- {abs_workspace}/departments/{department_type}/PLAN.md — Your task list
- {abs_workspace}/departments/{department_type}/MEMORY.md — Your persistent memory
- {abs_workspace}/knowledge/graph.jsonl — Knowledge graph
- {abs_workspace}/code/ — Product source code
- {abs_workspace}/content/ — Marketing content
- {abs_workspace}/site/ — Website assets
{tasks_section}{chat_section}
## Your Task for This Run
{task_description}

## Critical Instructions
1. Check STEERING.md first for human overrides
2. Read your PLAN.md to find the next unchecked task (- [ ])
3. Execute ONE task only (fresh context pattern — don't try to do everything)
4. Validate your work before marking complete
5. Be concise in your final summary — state what you did and what changed

## OUTPUT FORMAT (MANDATORY)
You CANNOT write files directly. Instead, output file changes using this exact format:

### File: <relative-path>
```
<full file content>
```

Examples:
### File: departments/{department_type}/PLAN.md
```
# {department_type.upper()} — Task Plan

## Tasks
- [x] Completed task
- [ ] Next task: description
```

### File: COMPANY.md
```
(full updated content)
```

Use relative paths from the company workspace root (e.g., `departments/ceo/PLAN.md`, `COMPANY.md`).
You MUST use this format for ALL file changes. Any text outside these blocks is treated as commentary only.
"""


async def _spawn_via_anthropic(
    company_slug: str,
    department_type: str,
    task_prompt: str,
    model: str,
    workspace: Path,
) -> dict:
    """
    Fallback: run the department task directly via Anthropic-compat API.
    Tries local proxy (ANTHROPIC_API_BASE) first, then direct Anthropic API (ANTHROPIC_API_KEY).
    Reads and writes files to workspace just like the OpenClaw agent would.
    """
    import os as _os2
    from app.config import settings

    # Map OpenClaw model names to bare model IDs
    MODEL_MAP = {
        "anthropic/claude-opus-4-6":    "claude-opus-4-6",
        "anthropic/claude-sonnet-4-6":  "claude-sonnet-4-6",
        "anthropic/claude-haiku-3.5":   "claude-haiku-4-5",
        "anthropic/claude-haiku-3-5":   "claude-haiku-4-5",
        "claude-opus-4-6":              "claude-opus-4-6",
        "claude-sonnet-4-6":            "claude-sonnet-4-6",
        "claude-haiku-3-5":             "claude-haiku-4-5",
    }
    api_model = MODEL_MAP.get(model, "claude-sonnet-4-6")

    # Local OpenAI-compat proxy (e.g. claude-openai-adapter)
    anthropic_base = (
        _os2.environ.get("ANTHROPIC_API_BASE")
        or getattr(settings, "ANTHROPIC_API_BASE", None)
        or "http://172.24.0.1:8322"  # CC-Bridge: OpenAI-compat proxy via Claude Max
    )
    anthropic_key = (
        _os2.environ.get("ANTHROPIC_API_KEY")
        or getattr(settings, "ANTHROPIC_API_KEY", None)
        or "dummy"  # local proxy may not need a real key
    )

    logger.info(
        f"[{company_slug}/{department_type}] Calling LLM "
        f"(base={anthropic_base}, model={api_model})"
    )

    # System prompt for the department role
    system_prompt = _get_role_description(department_type).strip()

    try:
        # Try OpenAI-compat format first (claude-openai-adapter uses /v1/chat/completions)
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{anthropic_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {anthropic_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": api_model,
                    "max_tokens": 4096,
                    "messages": [
                        *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                        {"role": "user", "content": task_prompt},
                    ],
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                output = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                _apply_agent_output(output, workspace, department_type)
                logger.info(f"[{company_slug}/{department_type}] LLM run completed ({len(output)} chars)")
                return {
                    "status": "accepted",
                    "output": output,
                    "model": api_model,
                    "department": department_type,
                    "company_slug": company_slug,
                }
            else:
                logger.warning(
                    f"[{company_slug}/{department_type}] LLM proxy {resp.status_code}: {resp.text[:200]}"
                )

    except httpx.ConnectError:
        logger.warning(f"[{company_slug}/{department_type}] LLM proxy unreachable at {anthropic_base}")
    except Exception as e:
        logger.warning(f"[{company_slug}/{department_type}] LLM proxy error: {e}")

    # Final fallback: Anthropic Python SDK (if real key is available)
    real_key = _os2.environ.get("ANTHROPIC_API_KEY") or getattr(settings, "ANTHROPIC_API_KEY", None)
    if real_key and real_key != "dummy":
        try:
            import anthropic
            client_sdk = anthropic.Anthropic(api_key=real_key)
            response = client_sdk.messages.create(
                model=api_model,
                max_tokens=4096,
                messages=[{"role": "user", "content": task_prompt}],
            )
            output = response.content[0].text if response.content else ""
            _apply_agent_output(output, workspace, department_type)
            logger.info(f"[{company_slug}/{department_type}] Anthropic SDK run completed ({len(output)} chars)")
            return {
                "status": "accepted",
                "output": output,
                "model": api_model,
                "department": department_type,
                "company_slug": company_slug,
            }
        except Exception as e:
            logger.error(f"[{company_slug}/{department_type}] Anthropic SDK error: {e}")
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "No LLM available: set ANTHROPIC_API_KEY or ensure local proxy is running"}


def _apply_agent_output(output: str, workspace: Path, department_type: str) -> None:
    """
    Parse agent output for file write instructions and apply them.
    Looks for markdown code blocks with file paths as titles.
    Example:
      ### File: departments/developer/PLAN.md
      ```
      content here
      ```
    """
    import re

    # Pattern: ### File: <path>\n```\n<content>\n```
    pattern = re.compile(
        r"###\s+(?:File|UPDATE|Write):\s*`?([^\n`]+)`?\n```[^\n]*\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(output):
        rel_path = match.group(1).strip()
        content = match.group(2)
        # Security: only allow writes within workspace
        try:
            target = (workspace / rel_path).resolve()
            if not str(target).startswith(str(workspace.resolve())):
                logger.warning(f"Blocked out-of-workspace write: {rel_path}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            logger.info(f"Agent wrote: {rel_path}")
        except Exception as e:
            logger.warning(f"Failed to write agent output file {rel_path}: {e}")


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
    Spawn an agent session.
    Primary: OpenClaw Gateway HTTP API.
    Fallback: Anthropic API directly (when gateway is unreachable from Docker).
    """
    workspace = get_company_workspace(company_id, company_slug)
    agent_id = DEPT_TO_AGENT.get(department_type, "coordinator")
    token = _get_gateway_token()

    # Model tiering
    if not model:
        model = get_model_for_department(department_type)

    task_prompt = _build_task_prompt(
        company_name=company_name,
        company_mission=company_mission,
        department_type=department_type,
        task_description=task_description,
        workspace=workspace,
        pending_tasks=pending_tasks,
        chat_history=chat_history,
    )

    # Try OpenClaw gateway first (works when running on the host)
    if token:
        spawn_args: dict = {
            "agentId": agent_id,
            "task": task_prompt,
            "cwd": str(workspace),
            "mode": "run",
            "runTimeoutSeconds": timeout_seconds,
        }
        if model:
            spawn_args["model"] = model

        logger.info(
            f"Spawning {department_type} agent via gateway (openclaw:{agent_id}, model:{model}) "
            f"for {company_slug}"
        )

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
                    timeout=30.0,
                )

                result = response.json()

                if result.get("ok"):
                    # Parse the nested result
                    content = result.get("result", {}).get("content", [])
                    details = {}
                    for item in content:
                        if item.get("type") == "text":
                            try:
                                details = json.loads(item["text"])
                            except (json.JSONDecodeError, KeyError):
                                pass

                    return {
                        "status": "accepted",
                        "session_key": details.get("childSessionKey"),
                        "run_id": details.get("runId"),
                        "agent_id": agent_id,
                        "department": department_type,
                        "company_slug": company_slug,
                        "model": model,
                    }
                else:
                    error = result.get("error", {})
                    logger.warning(f"Gateway spawn failed, falling back to Anthropic: {error}")

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"Gateway unreachable ({e}), falling back to Anthropic API")
        except Exception as e:
            logger.warning(f"Gateway error ({e}), falling back to Anthropic API")
    else:
        logger.info(f"No gateway token, using Anthropic API directly for {department_type}")

    # Fallback: Anthropic API
    return await _spawn_via_anthropic(company_slug, department_type, task_prompt, model, workspace)


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
