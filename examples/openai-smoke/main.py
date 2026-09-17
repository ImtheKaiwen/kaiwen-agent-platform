from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from kaiwen_agent import Agent, AgentContext
from kaiwen_agent.models.openai import OpenAIResponsesProvider
from kaiwen_agent.types import AgentInput

ROOT = Path(__file__).parents[2]


async def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing in the repository .env file")

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    agent = Agent(
        name="openai-smoke",
        model=OpenAIResponsesProvider(
            model=model,
            instructions="Reply with exactly: KAIWEN_AGENT_OK",
            store=False,
        ),
    )
    result = await agent.run(
        AgentInput(text="Run the connectivity check."),
        context=AgentContext(session_id="smoke-test"),
    )
    print(f"model={model}")
    print(f"status={result.status}")
    print(f"text={result.text.strip()}")
    print(f"tokens={result.usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())
