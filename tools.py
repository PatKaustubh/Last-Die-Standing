from __future__ import annotations

from .config import AppConfig
from .knowledge import LocalKnowledgeBase
from .storage import JsonMemoryStore

try:
    from agents import function_tool
except ImportError as exc:
    raise RuntimeError(
        "The OpenAI Agents SDK is not installed. Run `python -m pip install -e .`."
    ) from exc


_config = AppConfig.from_env()
_knowledge = LocalKnowledgeBase(_config.knowledge_dir)
_memory = JsonMemoryStore(_config.memory_dir)


@function_tool
def search_knowledge(query: str, limit: int = 5) -> str:
    """Search local files in data/knowledge for relevant project context."""
    hits = _knowledge.search(query=query, limit=limit)
    if not hits:
        return "No matching local knowledge found."

    return "\n".join(
        f"- {hit.path}:{hit.line} | score={hit.score} | {hit.preview}"
        for hit in hits
    )


@function_tool
def remember_memory(user_id: str, key: str, value: str) -> str:
    """Save an explicit user or project memory item."""
    item = _memory.remember(user_id=user_id, key=key, value=value)
    return f"Saved memory `{item.key}` for user `{user_id}`."


@function_tool
def recall_memory(user_id: str, query: str = "", limit: int = 5) -> str:
    """Recall explicit user or project memory items."""
    items = _memory.recall(user_id=user_id, query=query or None, limit=limit)
    if not items:
        return "No matching memory found."

    return "\n".join(
        f"- {item.key}: {item.value} (updated {item.updated_at})" for item in items
    )
