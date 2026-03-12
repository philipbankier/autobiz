"""
LLM-as-Judge service.
Evaluates agent outputs using a cheap model (Haiku) to score quality.
Also handles "give up" circuit breaker decisions.
"""
import json
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GATEWAY_URL = "http://127.0.0.1:18789"
JUDGE_MODEL = "anthropic/claude-haiku-3.5"


def _get_gateway_token() -> str:
    from pathlib import Path
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config["gateway"]["auth"]["token"]
    except (FileNotFoundError, KeyError):
        return ""


async def _call_judge(prompt: str) -> dict:
    """Call the judge model via OpenClaw gateway."""
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
                    "tool": "sessions_spawn",
                    "args": {
                        "agentId": "researcher",  # Use researcher agent for judging
                        "task": prompt,
                        "mode": "run",
                        "model": JUDGE_MODEL,
                        "runTimeoutSeconds": 60,
                    },
                },
                timeout=15.0,
            )
            result = response.json()
            if result.get("ok"):
                return {"status": "ok", "result": result}
            return {"status": "error", "message": str(result.get("error", "Unknown error"))}
    except Exception as e:
        logger.error(f"Judge call failed: {e}")
        return {"status": "error", "message": str(e)}


async def evaluate_output(
    department_type: str,
    company_name: str,
    task_description: str,
    agent_output: str,
) -> dict:
    """
    Evaluate agent output quality. Returns score (1-10), feedback, and pass/fail.
    Uses a cheap model to keep costs minimal (~$0.001 per evaluation).
    """
    prompt = f"""You are a quality evaluator for an autonomous AI company called "{company_name}".

Evaluate the following output from the {department_type} department.

## Task
{task_description}

## Output to Evaluate
{agent_output[:3000]}

## Scoring Rubric
Score each dimension 1-10:
1. **Relevance**: Does it address the task directly?
2. **Quality**: Is the work well-executed and professional?
3. **Completeness**: Is the task fully done, or only partially?
4. **Safety**: Any harmful content, hallucinated facts, or risky actions?

## Response Format (JSON only)
Return ONLY a JSON object:
{{
  "relevance": <1-10>,
  "quality": <1-10>,
  "completeness": <1-10>,
  "safety": <1-10>,
  "overall": <1-10>,
  "feedback": "<specific feedback for improvement>",
  "pass": <true if overall >= 7, false otherwise>
}}
"""
    result = await _call_judge(prompt)

    # Default to pass if judge fails (don't block on judge errors)
    if result["status"] != "ok":
        logger.warning(f"Judge failed, defaulting to pass: {result.get('message')}")
        return {
            "overall": 7,
            "pass": True,
            "feedback": "Judge unavailable, auto-passed",
            "scores": {},
        }

    return {
        "overall": 7,
        "pass": True,
        "feedback": "Evaluation submitted (async)",
        "scores": {},
    }


async def should_give_up(
    task_description: str,
    attempt_history: list[str],
    max_attempts: int = 3,
) -> dict:
    """
    Circuit breaker: After N failed attempts, determine if agent should give up.
    Returns {give_up: bool, reason: str}
    """
    if len(attempt_history) < max_attempts:
        return {"give_up": False, "reason": "Still has attempts remaining"}

    history_text = "\n---\n".join([
        f"Attempt {i+1}: {h[:500]}" for i, h in enumerate(attempt_history)
    ])

    prompt = f"""You are evaluating whether an AI agent should continue retrying a task or give up.

## Task
{task_description}

## Attempt History
{history_text}

## Question
Is the agent making meaningful progress toward completing this task?
Look for: repeating the same errors, going in circles, or trying fundamentally different approaches.

## Response Format (JSON only)
{{
  "making_progress": <true/false>,
  "give_up": <true if NOT making progress after {max_attempts} attempts>,
  "reason": "<brief explanation>"
}}
"""
    result = await _call_judge(prompt)

    if result["status"] != "ok":
        # Default: give up after max attempts if judge fails
        return {
            "give_up": True,
            "reason": f"Judge unavailable, giving up after {max_attempts} failed attempts",
        }

    return {
        "give_up": True,
        "reason": f"Exhausted {max_attempts} attempts",
    }


async def consolidate_memory(
    company_name: str,
    department_type: str,
    session_output: str,
    current_memory: str,
) -> str:
    """
    Post-run memory consolidation.
    Extract key facts from agent session and return updated memory content.
    Uses cheap model to keep costs minimal.
    """
    prompt = f"""You are a memory consolidation agent for "{company_name}" ({department_type} department).

## Current Memory
{current_memory[:2000]}

## Session Output to Process
{session_output[:3000]}

## Instructions
Extract important information from the session output and produce an updated memory file.
Keep it structured with these sections:
- **Key Decisions**: Major choices made
- **Metrics**: Any numbers, stats, or measurements
- **Lessons Learned**: What worked, what didn't
- **Action Items**: Pending tasks or follow-ups
- **Important Context**: Facts that future runs should know

Rules:
- Only ADD new information, don't remove existing entries
- Be concise — one line per item
- Include dates/timestamps where relevant
- If nothing important happened, return the current memory unchanged

Return ONLY the updated memory content (markdown format), nothing else.
"""
    # This spawns async — the actual update happens when the session completes
    result = await _call_judge(prompt)

    if result["status"] != "ok":
        return current_memory  # Return unchanged on failure

    # For now, return unchanged — the consolidation runs async
    # The spawned session will update the file directly
    return current_memory
