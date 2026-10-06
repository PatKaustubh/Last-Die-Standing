from __future__ import annotations

from .config import AppConfig
from .tools import recall_memory, remember_memory, search_knowledge

try:
    from agents import Agent
except ImportError as exc:
    raise RuntimeError(
        "The OpenAI Agents SDK is not installed. Run `python -m pip install -e .`."
    ) from exc

try:
    from agents import WebSearchTool
except ImportError:
    WebSearchTool = None  # type: ignore[assignment]


def build_agent_system(config: AppConfig | None = None) -> Agent:
    config = config or AppConfig.from_env()

    research_tools = [search_knowledge]
    if config.enable_web_search and WebSearchTool is not None:
        research_tools.append(WebSearchTool())

    researcher = Agent(
        name="Research Agent",
        model=config.model,
        handoff_description="Finds relevant facts from local knowledge and optional web search.",
        instructions=(
            "You are a careful research specialist. Search local knowledge first. "
            "If web search is available and needed, use it to fill gaps. "
            "Return concise findings with source names or file references."
        ),
        tools=research_tools,
    )

    planner = Agent(
        name="Planning Agent",
        model=config.model,
        handoff_description="Turns rough goals into practical plans and milestones.",
        instructions=(
            "You are a pragmatic planning specialist. Convert ambiguous goals into "
            "small, ordered steps with assumptions, risks, and a next action. "
            "Prefer concrete milestones over abstract strategy."
        ),
        tools=[search_knowledge, recall_memory],
    )

    return Agent(
        name="Coordinator Agent",
        model=config.model,
        instructions=(
            "You are the front-door agent for a personal AI agent system. "
            "Help the user turn goals into working plans and useful outputs. "
            f"The current user id is `{config.user_id}`. "
            "Use recall_memory when past preferences or project facts may matter. "
            "Use remember_memory only for explicit stable facts the user asks you to keep. "
            "Use search_knowledge before relying on unstated project details. "
            "Handoff to the Research Agent for fact-finding and the Planning Agent for "
            "multi-step project planning. Ask a clarifying question only when a "
            "reasonable assumption would create real risk."
        ),
        tools=[search_knowledge, recall_memory, remember_memory],
        handoffs=[researcher, planner],
    )
