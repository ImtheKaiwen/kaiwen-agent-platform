from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from kaiwen_agent import Agent, AgentContext, tool
from kaiwen_agent.models.openai import OpenAIResponsesProvider
from kaiwen_agent.types import AgentInput
from pydantic import BaseModel

ROOT = Path(__file__).parents[2]


class ConnectivityInput(BaseModel):
    value: Literal["ping"]


@tool(
    name="connectivity.check",
    description="Run the required connectivity check.",
    input_model=ConnectivityInput,
    permissions={"connectivity.read"},
)
async def check_connectivity(
    context: AgentContext, arguments: ConnectivityInput
) -> dict[str, str]:
    del context, arguments
    return {"status": "ok"}


async def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing in the repository .env file")

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    agent = Agent(
        name="openai-smoke",
        model=OpenAIResponsesProvider(
            model=model,
            instructions=(
                "Call connectivity.check with value ping. After the tool succeeds, "
                "reply with exactly: KAIWEN_AGENT_OK"
            ),
            store=False,
        ),
        tools=[check_connectivity],
        permissions={"connectivity.read"},
    )
    result = await agent.run(
        AgentInput(text="Run the connectivity check."),
        context=AgentContext(
            session_id="smoke-test",
            permissions=frozenset({"connectivity.read"}),
        ),
    )
    print(f"model={model}")
    print(f"status={result.status}")
    print(f"text={result.text.strip()}")
    print(f"tools={','.join(item.name for item in result.tool_results)}")
    print(f"tokens={result.usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())
