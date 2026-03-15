"""
LLM-as-Judge service.
Evaluates agent outputs using direct Anthropic API calls (Haiku) to score quality.
Also handles "give up" circuit breaker decisions and memory consolidation.
"""
import json
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
JUDGE_MODEL = "claude-haiku-4-5-20241022"


def _get_api_key() -> str:
    """Get Anthropic API key from settings env or OpenClaw config."""
    if settings.ANTHROPIC_API_KEY:
        return settings.ANTHROPIC_API_KEY

    # Fallback: read from OpenClaw config
    from pathlib import Path
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config["providers"]["anthropic"]["apiKey"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return ""


async def _call_anthropic(prompt: str, max_tokens: int = 1000) -> str:
    """Make a direct HTTP call to Anthropic API. Returns the text response."""
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("No Anthropic API key configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": JUDGE_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        # Extract text from content blocks
        for block in data.get("content", []):
            if block.get("type") == "text":
                return block["text"]
        return ""


def _parse_json_response(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code fences."""
    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        lines = [l for l in lines[1:] if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


async def evaluate_output(
    department_type: str,
    company_name: str,
    task_description: str,
    agent_output: str,
) -> dict:
    """
    Evaluate agent output quality. Returns score (1-10), feedback, and pass/fail.
    Uses Haiku for minimal cost (~$0.001 per evaluation).
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
  "pass": <true if overall >= 6, false otherwise>
}}
"""
    try:
        raw = await _call_anthropic(prompt)
        parsed = _parse_json_response(raw)

        if not parsed or "overall" not in parsed:
            logger.warning(f"Judge returned unparseable response: {raw[:200]}")
            return {
                "overall": 7,
                "pass": True,
                "feedback": "Judge response unparseable, auto-passed",
                "scores": {},
            }

        return {
            "overall": parsed["overall"],
            "pass": parsed.get("pass", parsed["overall"] >= 6),
            "feedback": parsed.get("feedback", ""),
            "scores": {
                k: parsed[k]
                for k in ("relevance", "quality", "completeness", "safety")
                if k in parsed
            },
        }
    except Exception as e:
        logger.warning(f"Judge evaluation failed, defaulting to pass: {e}")
        return {
            "overall": 7,
            "pass": True,
            "feedback": f"Judge unavailable ({e}), auto-passed",
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
    try:
        raw = await _call_anthropic(prompt, max_tokens=500)
        parsed = _parse_json_response(raw)

        if not parsed or "give_up" not in parsed:
            return {
                "give_up": True,
                "reason": f"Judge unparseable, giving up after {max_attempts} attempts",
            }

        return {
            "give_up": parsed["give_up"],
            "reason": parsed.get("reason", "No reason given"),
        }
    except Exception as e:
        logger.warning(f"Judge give-up check failed: {e}")
        return {
            "give_up": True,
            "reason": f"Judge unavailable, giving up after {max_attempts} failed attempts",
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
    Returns the updated memory string, or current_memory unchanged on failure.
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
    try:
        result = await _call_anthropic(prompt, max_tokens=2000)
        result = result.strip()

        # Sanity check: non-empty and looks like markdown
        if not result or len(result) < 20:
            return current_memory

        return result
    except Exception as e:
        logger.warning(f"Memory consolidation failed: {e}")
        return current_memory
