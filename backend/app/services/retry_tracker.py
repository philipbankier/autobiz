"""
Retry tracking for agent task quality gates.
Tracks how many times a task has been attempted after judge failures.
Storage: companies/{slug}/departments/{dept}/retries.json
"""
import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")


def _task_id(task_text: str) -> str:
    """Generate a stable task ID from task text (first 8 chars of md5)."""
    return hashlib.md5(task_text.encode()).hexdigest()[:8]


def _retries_path(slug: str, dept: str) -> Path:
    return COMPANIES_DIR / slug / "departments" / dept / "retries.json"


def _load_retries(slug: str, dept: str) -> dict:
    path = _retries_path(slug, dept)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_retries(slug: str, dept: str, data: dict) -> None:
    path = _retries_path(slug, dept)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def get_retry_count(slug: str, dept: str, task_id: str) -> int:
    data = _load_retries(slug, dept)
    entry = data.get(task_id, {})
    return entry.get("count", 0)


def get_attempt_history(slug: str, dept: str, task_id: str) -> list[str]:
    data = _load_retries(slug, dept)
    entry = data.get(task_id, {})
    return entry.get("history", [])


def increment_retry(slug: str, dept: str, task_id: str, feedback: str = "") -> int:
    """Increment retry count and append feedback to history. Returns new count."""
    data = _load_retries(slug, dept)
    if task_id not in data:
        data[task_id] = {"count": 0, "history": []}
    data[task_id]["count"] += 1
    if feedback:
        data[task_id]["history"].append(feedback)
    _save_retries(slug, dept, data)
    return data[task_id]["count"]


def clear_retry(slug: str, dept: str, task_id: str) -> None:
    data = _load_retries(slug, dept)
    data.pop(task_id, None)
    _save_retries(slug, dept, data)


def get_all_retries(slug: str, dept: str) -> dict:
    return _load_retries(slug, dept)
