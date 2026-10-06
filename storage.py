from __future__ import annotations

import json
import re
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


_SAFE_ID = re.compile(r"[^a-zA-Z0-9_.-]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_name(value: str) -> str:
    cleaned = _SAFE_ID.sub("-", value.strip()).strip("-")
    return cleaned or "default"


@dataclass(frozen=True)
class MemoryItem:
    key: str
    value: str
    created_at: str
    updated_at: str


class JsonMemoryStore:
    """A tiny explicit-memory store for local development."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self._lock = threading.Lock()

    def remember(self, user_id: str, key: str, value: str) -> MemoryItem:
        user_id = _safe_name(user_id)
        key = _safe_name(key)

        with self._lock:
            self.root.mkdir(parents=True, exist_ok=True)
            data = self._read_user_memory(user_id)
            current_time = _now()
            existing = data.get(key, {})
            item = MemoryItem(
                key=key,
                value=value,
                created_at=existing.get("created_at", current_time),
                updated_at=current_time,
            )
            data[key] = asdict(item)
            self._write_user_memory(user_id, data)
            return item

    def recall(
        self, user_id: str, query: str | None = None, limit: int = 5
    ) -> list[MemoryItem]:
        data = self._read_user_memory(_safe_name(user_id))
        items = [MemoryItem(**item) for item in data.values()]

        if query:
            terms = [term.lower() for term in query.split() if term.strip()]
            items = [
                item
                for item in items
                if all(
                    term in item.key.lower() or term in item.value.lower()
                    for term in terms
                )
            ]

        return sorted(items, key=lambda item: item.updated_at, reverse=True)[:limit]

    def _path_for_user(self, user_id: str) -> Path:
        return self.root / f"{user_id}.json"

    def _read_user_memory(self, user_id: str) -> dict[str, dict[str, str]]:
        path = self._path_for_user(user_id)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            return {}
        return payload

    def _write_user_memory(self, user_id: str, data: dict[str, dict[str, str]]) -> None:
        path = self._path_for_user(user_id)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
