from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(PROJECT_ROOT / ".env")


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    model: str
    user_id: str
    max_turns: int
    enable_web_search: bool
    api_token: str | None
    cors_origins: tuple[str, ...]
    trace_include_sensitive_data: bool
    project_root: Path
    knowledge_dir: Path
    memory_dir: Path

    @classmethod
    def from_env(cls) -> "AppConfig":
        _load_dotenv_if_available()

        return cls(
            model=os.getenv("AGENT_MODEL", "gpt-5.5"),
            user_id=os.getenv("AGENT_USER_ID", "local-user"),
            max_turns=_int_env("AGENT_MAX_TURNS", 10),
            enable_web_search=_bool_env("AGENT_ENABLE_WEB_SEARCH", False),
            api_token=os.getenv("AGENT_API_TOKEN") or None,
            cors_origins=tuple(
                origin.strip()
                for origin in os.getenv("AGENT_CORS_ORIGINS", "*").split(",")
                if origin.strip()
            ),
            trace_include_sensitive_data=_bool_env(
                "OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA", False
            ),
            project_root=PROJECT_ROOT,
            knowledge_dir=PROJECT_ROOT / "data" / "knowledge",
            memory_dir=PROJECT_ROOT / "data" / "memory",
        )
