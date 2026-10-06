from __future__ import annotations

import os

from .agents import build_agent_system
from .config import AppConfig


def configure_tracing(config: AppConfig) -> None:
    if not config.trace_include_sensitive_data:
        os.environ.setdefault("OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA", "false")


def require_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured.")


def with_context(prompt: str, config: AppConfig, user_id: str | None = None) -> str:
    active_user_id = user_id or config.user_id
    return f"User id: {active_user_id}\n\nUser request:\n{prompt}"


async def run_agent(prompt: str, config: AppConfig, user_id: str | None = None) -> str:
    from agents import Runner

    require_api_key()
    configure_tracing(config)
    agent = build_agent_system(config)
    result = await Runner.run(
        agent,
        with_context(prompt, config, user_id=user_id),
        max_turns=config.max_turns,
    )
    return str(result.final_output)
