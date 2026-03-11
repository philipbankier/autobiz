"""
OpenClaw integration service.
Spawns and manages agent sessions for company departments.
"""
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

OPENCLAW_BIN = "/home/philip/.nvm/versions/node/v22.19.0/bin/openclaw"
COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")

# Map AutoBiz department types to OpenClaw agent names
DEPT_TO_AGENT = {
    "ceo": "orchestrator",
    "developer": "developer",
    "marketing": "marketing",
    "sales": "marketing",  # Sales shares marketing agent for now
    "finance": "researcher",  # Finance uses researcher for analysis
    "support": "main",  # Support uses main agent
}


def get_company_workspace(company_id: str, slug: str) -> Path:
    """Get or create workspace directory for a company."""
    workspace = COMPANIES_DIR / slug
    workspace.mkdir(parents=True, exist_ok=True)

    # Create knowledge graph file if not exists
    kg_file = workspace / "knowledge-graph.jsonl"
    if not kg_file.exists():
        kg_file.write_text("")

    # Create COMPANY.md context file if not exists
    company_md = workspace / "COMPANY.md"
    if not company_md.exists():
        company_md.write_text(f"# Company: {slug}\nID: {company_id}\n")

    return workspace


def build_agent_prompt(
    company_name: str,
    company_mission: str,
    department_type: str,
    task_description: str,
    knowledge_context: str = "",
    pending_tasks: list[dict] | None = None,
    chat_history: list[dict] | None = None,
) -> str:
    """Build a contextual prompt for an agent session."""

    tasks_section = ""
    if pending_tasks:
        tasks_section = "\n## Pending Tasks\n"
        for t in pending_tasks:
            tasks_section += f"- [{t['priority']}] {t['title']}: {t['description']}\n"

    chat_section = ""
    if chat_history:
        chat_section = "\n## Recent Messages from Human Owner\n"
        for msg in chat_history[-5:]:  # Last 5 messages
            chat_section += f"- {msg['role']}: {msg['content']}\n"

    kg_section = ""
    if knowledge_context:
        kg_section = f"\n## Knowledge Graph Context\n{knowledge_context}\n"

    prompt = f"""You are the {department_type.upper()} department of {company_name}.

## Company Mission
{company_mission}

## Your Role
You are the {department_type} agent. You operate autonomously to advance the company mission.
{_get_role_instructions(department_type)}
{tasks_section}{chat_section}{kg_section}
## Instructions
1. Review the current state of the company and your pending tasks.
2. Execute the most impactful work you can right now.
3. After completing work, write a brief summary of what you did.
4. If you created any files, they should be in the company workspace.
5. Update the knowledge graph with any new entities or decisions.

## Current Task
{task_description}

When finished, output a JSON summary on the LAST line:
{{"status": "completed", "summary": "what you did", "files_created": [], "files_modified": [], "entities_added": []}}
"""
    return prompt


def _get_role_instructions(department_type: str) -> str:
    """Department-specific instructions."""
    instructions = {
        "ceo": """As CEO, you:
- Review overall company progress and metrics
- Create and prioritize tasks for other departments
- Make strategic decisions about product direction
- Ensure all departments are aligned with the mission""",

        "developer": """As Developer, you:
- Build and maintain the product (code, deploy, test)
- Fix bugs and implement features from your task list
- Write clean, production-ready code
- Deploy to Vercel/Cloudflare when ready""",

        "marketing": """As Marketing, you:
- Create compelling content (blog posts, social media, threads)
- Plan and execute marketing campaigns
- Write copy for the website and landing pages
- Research and engage target audience""",

        "sales": """As Sales, you:
- Optimize landing pages for conversion
- Create lead magnets and signup flows
- Analyze pricing strategy
- Track and improve conversion metrics""",

        "finance": """As Finance, you:
- Track revenue, costs, and profitability
- Create financial reports and projections
- Monitor agent spending and ROI
- Recommend budget adjustments""",

        "support": """As Support, you:
- Monitor and respond to customer inquiries
- Categorize and prioritize issues
- Create FAQ and help documentation
- Escalate critical issues to CEO""",
    }
    return instructions.get(department_type, "Execute your assigned tasks efficiently.")


async def run_agent_session(
    company_id: str,
    company_slug: str,
    company_name: str,
    company_mission: str,
    department_type: str,
    task_description: str,
    knowledge_context: str = "",
    pending_tasks: list[dict] | None = None,
    chat_history: list[dict] | None = None,
) -> dict:
    """
    Run an agent session via OpenClaw CLI.
    Returns the agent's response and any artifacts.
    """
    workspace = get_company_workspace(company_id, company_slug)
    agent_name = DEPT_TO_AGENT.get(department_type, "main")

    prompt = build_agent_prompt(
        company_name=company_name,
        company_mission=company_mission,
        department_type=department_type,
        task_description=task_description,
        knowledge_context=knowledge_context,
        pending_tasks=pending_tasks,
        chat_history=chat_history,
    )

    logger.info(f"Running {department_type} agent for {company_slug} (agent: {agent_name})")

    try:
        # Use claude CLI directly with the agent's context
        result = subprocess.run(
            [
                "claude",
                "--permission-mode", "bypassPermissions",
                "--print",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max per agent run
            cwd=str(workspace),
            env={
                "PATH": "/home/philip/.nvm/versions/node/v22.19.0/bin:/usr/local/bin:/usr/bin:/bin",
                "HOME": "/home/philip",
            },
        )

        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.error(f"Agent failed: {stderr}")
            return {
                "status": "failed",
                "summary": f"Agent error: {stderr[:500]}",
                "output": output[:2000],
                "tokens_used": 0,
                "cost": 0,
            }

        # Try to parse the JSON summary from the last line
        summary = _extract_summary(output)

        return {
            "status": summary.get("status", "completed"),
            "summary": summary.get("summary", output[-500:] if len(output) > 500 else output),
            "output": output,
            "files_created": summary.get("files_created", []),
            "files_modified": summary.get("files_modified", []),
            "entities_added": summary.get("entities_added", []),
            "tokens_used": _estimate_tokens(prompt, output),
            "cost": _estimate_cost(prompt, output),
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Agent timed out for {department_type}/{company_slug}")
        return {
            "status": "failed",
            "summary": "Agent timed out after 5 minutes",
            "output": "",
            "tokens_used": 0,
            "cost": 0,
        }
    except Exception as e:
        logger.error(f"Agent exception: {e}")
        return {
            "status": "failed",
            "summary": f"Agent exception: {str(e)[:500]}",
            "output": "",
            "tokens_used": 0,
            "cost": 0,
        }


def _extract_summary(output: str) -> dict:
    """Try to extract JSON summary from agent output."""
    # Look for JSON on the last few lines
    lines = output.strip().split("\n")
    for line in reversed(lines[-10:]):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {}


def _estimate_tokens(prompt: str, output: str) -> int:
    """Rough token estimate (4 chars per token)."""
    return (len(prompt) + len(output)) // 4


def _estimate_cost(prompt: str, output: str) -> float:
    """Rough cost estimate based on Claude Sonnet pricing."""
    input_tokens = len(prompt) // 4
    output_tokens = len(output) // 4
    # Sonnet: $3/M input, $15/M output
    cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000
    return round(cost, 4)
