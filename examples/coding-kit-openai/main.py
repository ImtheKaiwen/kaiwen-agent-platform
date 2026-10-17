from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from kaiwen_agent.agents import AgentDefinitionRegistry
from kaiwen_agent.capabilities import CapabilityRegistry
from kaiwen_agent.kits.coding import (
    CodingConversationPreferences,
    CodingKitConfig,
    CodingKitFactory,
    CodingUserLanguage,
)
from kaiwen_agent.models import OpenAIResponsesProvider, ProviderRegistry
from kaiwen_agent.prompts import PromptRegistry
from kaiwen_agent.runtime import AgentFactory, RuntimeIdentity
from kaiwen_agent.standards import StandardsRegistry
from kaiwen_agent.tools.registry import ToolRegistry

ROOT = Path(__file__).parents[2]


async def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not configured")
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    providers = ProviderRegistry()
    providers.register(
        "openai:coding",
        lambda instructions: OpenAIResponsesProvider(
            model=model, instructions=instructions, store=False
        ),
    )
    factory = AgentFactory(
        agents=AgentDefinitionRegistry(),
        prompts=PromptRegistry(),
        capabilities=CapabilityRegistry(),
        providers=providers,
        tools=ToolRegistry(),
        standards=StandardsRegistry(),
    )
    agent = CodingKitFactory(factory).create(CodingKitConfig(provider_ref="openai:coding"))
    preference = CodingConversationPreferences(user_language=CodingUserLanguage.TURKISH)
    result = await agent.chat(
        "Yalnızca 'Hazır.' yazarak cevap ver.",
        identity=RuntimeIdentity(
            session_id="coding-openai-example",
            metadata={"conversation_preferences": preference.model_dump(mode="json")},
        ),
    )
    print(result.text)
    print(f"tokens={result.usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())
