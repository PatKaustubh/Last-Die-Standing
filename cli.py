from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from .config import AppConfig
from .runtime import configure_tracing, require_api_key, run_agent, with_context


async def run_once(prompt: str, config: AppConfig) -> str:
    return await run_agent(prompt, config)


async def run_chat(config: AppConfig) -> None:
    from agents import Runner
    from .agents import build_agent_system

    agent = build_agent_system(config)
    history = None

    print("Agent chat started. Type /exit to quit.")
    while True:
        prompt = input("\nYou> ").strip()
        if prompt.lower() in {"/exit", "exit", "quit"}:
            return
        if not prompt:
            continue

        if history is None:
            turn_input = with_context(prompt, config)
        else:
            turn_input = history + [
                {"role": "user", "content": with_context(prompt, config)}
            ]

        result = await Runner.run(agent, turn_input, max_turns=config.max_turns)
        print(f"\nAgent> {result.final_output}")
        history = result.to_input_list()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AI agent system.")
    parser.add_argument("prompt", nargs="*", help="Prompt to send to the agent.")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode.")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig.from_env()

    configure_tracing(config)
    try:
        require_api_key()
    except RuntimeError as exc:
        raise SystemExit(
            "OPENAI_API_KEY is not set. Configure it as a cloud environment variable."
        ) from exc

    if args.chat:
        asyncio.run(run_chat(config))
        return

    prompt = " ".join(args.prompt).strip()
    if not prompt:
        parser.error("Provide a prompt or use --chat.")

    output = asyncio.run(run_once(prompt, config))
    print(output)


if __name__ == "__main__":
    main()
