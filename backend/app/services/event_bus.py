"""
In-memory async event bus for real-time SSE activity streaming.
Supports per-company event isolation, ring buffer replay, and sync publishing from Celery.
"""
import asyncio
import logging
import time
from collections import deque
from enum import Enum
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    agent_started = "agent_started"
    agent_completed = "agent_completed"
    agent_failed = "agent_failed"
    task_completed = "task_completed"
    deploy_started = "deploy_started"
    deploy_completed = "deploy_completed"
    budget_warning = "budget_warning"
    budget_exceeded = "budget_exceeded"
    run_skipped = "run_skipped"
    steering_changed = "steering_changed"


# Global state
_subscribers: dict[str, list[asyncio.Queue]] = {}  # company_id -> [queues]
_history: dict[str, deque] = {}  # company_id -> ring buffer of last 50 events
_event_counter: int = 0
_loop: asyncio.AbstractEventLoop | None = None


def _get_history(company_id: str) -> deque:
    if company_id not in _history:
        _history[company_id] = deque(maxlen=50)
    return _history[company_id]


def _make_event(
    event_type: EventType,
    department: str | None,
    message: str,
    data: dict | None = None,
) -> dict:
    global _event_counter
    _event_counter += 1
    return {
        "id": _event_counter,
        "type": event_type.value if isinstance(event_type, EventType) else event_type,
        "department": department,
        "message": message,
        "timestamp": time.time(),
        "data": data,
    }


async def publish(
    company_id: str,
    event_type: EventType | str,
    department: str | None = None,
    message: str = "",
    data: dict | None = None,
) -> None:
    """Publish an event to all subscribers of a company."""
    event = _make_event(event_type, department, message, data)
    _get_history(company_id).append(event)

    queues = _subscribers.get(company_id, [])
    for q in queues:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass  # Drop if subscriber is too slow


def publish_sync(
    company_id: str,
    event_type: EventType,
    department: str | None = None,
    message: str = "",
    data: dict | None = None,
) -> None:
    """Sync wrapper for publishing from Celery tasks.

    Tries to schedule on the running event loop. Falls back to
    direct buffer append if no loop is available (e.g. Celery worker
    without a running asyncio loop).
    """
    global _loop
    event = _make_event(event_type, department, message, data)
    _get_history(company_id).append(event)

    queues = _subscribers.get(company_id, [])
    if not queues:
        return

    # Try to push to subscriber queues
    if _loop and _loop.is_running():
        for q in queues:
            _loop.call_soon_threadsafe(q.put_nowait, event)
    else:
        # Direct append — works if in same process (e.g. in-process Celery)
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Called on FastAPI startup to capture the running event loop."""
    global _loop
    _loop = loop


async def subscribe(company_id: str) -> AsyncGenerator[dict, None]:
    """Yield events for a company. Replays history first, then streams live."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=256)

    # Register
    if company_id not in _subscribers:
        _subscribers[company_id] = []
    _subscribers[company_id].append(queue)

    try:
        # Replay history
        for event in _get_history(company_id):
            yield event

        # Stream live events
        while True:
            event = await queue.get()
            yield event
    finally:
        # Cleanup on disconnect
        try:
            _subscribers[company_id].remove(queue)
            if not _subscribers[company_id]:
                del _subscribers[company_id]
        except (ValueError, KeyError):
            pass


def get_recent_events(company_id: str, limit: int = 50) -> list[dict]:
    """Get recent events from the ring buffer."""
    history = _get_history(company_id)
    events = list(history)
    if limit and limit < len(events):
        events = events[-limit:]
    return events
