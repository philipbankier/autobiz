"""
Knowledge Graph service.
Stores entities and relations in a JSONL file per company (MCP-compatible format).
Phase 2: file-based. Phase 3: migrate to PostgreSQL + vector search.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

COMPANIES_DIR = Path("/home/philip/TinkerLab/autobiz/companies")

# Entity types
ENTITY_TYPES = [
    "company", "product", "customer", "competitor", "decision",
    "lesson", "metric", "content", "task", "feature",
]

# Relation types
RELATION_TYPES = [
    "owns", "uses", "built_with", "depends_on",
    "decided_by", "resulted_in", "learned_from",
    "targets", "converted_to", "churned_from",
    "outperforms", "competes_with",
]


def _kg_path(company_slug: str) -> Path:
    """Get knowledge graph file path for a company."""
    path = COMPANIES_DIR / company_slug / "knowledge-graph.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("")
    return path


def add_entity(
    company_slug: str,
    entity_type: str,
    name: str,
    properties: dict | None = None,
    source_department: str = "system",
) -> dict:
    """Add an entity to the knowledge graph."""
    entity = {
        "id": str(uuid4()),
        "kind": "entity",
        "type": entity_type,
        "name": name,
        "properties": properties or {},
        "source": source_department,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    path = _kg_path(company_slug)
    with open(path, "a") as f:
        f.write(json.dumps(entity) + "\n")

    logger.info(f"KG: Added entity '{name}' ({entity_type}) for {company_slug}")
    return entity


def add_relation(
    company_slug: str,
    from_entity: str,
    relation: str,
    to_entity: str,
    properties: dict | None = None,
    source_department: str = "system",
) -> dict:
    """Add a relation between entities."""
    rel = {
        "id": str(uuid4()),
        "kind": "relation",
        "from": from_entity,
        "relation": relation,
        "to": to_entity,
        "properties": properties or {},
        "source": source_department,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    path = _kg_path(company_slug)
    with open(path, "a") as f:
        f.write(json.dumps(rel) + "\n")

    logger.info(f"KG: Added relation '{from_entity}' -{relation}-> '{to_entity}' for {company_slug}")
    return rel


def add_decision(
    company_slug: str,
    what: str,
    why: str,
    decided_by: str = "ceo",
) -> dict:
    """Shortcut to record a decision."""
    return add_entity(
        company_slug,
        "decision",
        what,
        {"why": why, "decided_by": decided_by},
        source_department=decided_by,
    )


def add_lesson(
    company_slug: str,
    what_happened: str,
    what_we_learned: str,
    source_department: str = "system",
) -> dict:
    """Shortcut to record a lesson learned."""
    return add_entity(
        company_slug,
        "lesson",
        what_happened,
        {"learned": what_we_learned},
        source_department=source_department,
    )


def add_metric(
    company_slug: str,
    name: str,
    value: float | str,
    source_department: str = "finance",
) -> dict:
    """Record a metric."""
    return add_entity(
        company_slug,
        "metric",
        name,
        {"value": value, "date": datetime.now(timezone.utc).date().isoformat()},
        source_department=source_department,
    )


def get_entities(
    company_slug: str,
    entity_type: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Query entities from the knowledge graph."""
    path = _kg_path(company_slug)
    entities = []

    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if item.get("kind") == "entity":
                        if entity_type is None or item.get("type") == entity_type:
                            entities.append(item)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return []

    return entities[-limit:]  # Most recent


def get_context_summary(company_slug: str, max_items: int = 20) -> str:
    """Get a text summary of the knowledge graph for agent context."""
    path = _kg_path(company_slug)
    items = []

    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return "No knowledge graph entries yet."

    if not items:
        return "No knowledge graph entries yet."

    # Take the most recent items
    recent = items[-max_items:]
    lines = []
    for item in recent:
        if item.get("kind") == "entity":
            props = item.get("properties", {})
            props_str = ", ".join(f"{k}={v}" for k, v in props.items()) if props else ""
            lines.append(f"[{item['type']}] {item['name']}{' (' + props_str + ')' if props_str else ''}")
        elif item.get("kind") == "relation":
            lines.append(f"{item['from']} --{item['relation']}--> {item['to']}")

    return "\n".join(lines)


def get_stats(company_slug: str) -> dict:
    """Get knowledge graph statistics."""
    path = _kg_path(company_slug)
    entity_count = 0
    relation_count = 0
    types: dict[str, int] = {}

    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if item.get("kind") == "entity":
                        entity_count += 1
                        t = item.get("type", "unknown")
                        types[t] = types.get(t, 0) + 1
                    elif item.get("kind") == "relation":
                        relation_count += 1
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass

    return {
        "entities": entity_count,
        "relations": relation_count,
        "types": types,
    }
