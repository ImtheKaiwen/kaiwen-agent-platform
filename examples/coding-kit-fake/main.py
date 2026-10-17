from __future__ import annotations

import asyncio

from kaiwen_agent.agents import AgentDefinitionRegistry
from kaiwen_agent.capabilities import CapabilityRegistry
from kaiwen_agent.kits.coding import CodingKitConfig, CodingKitFactory
from kaiwen_agent.models import FakeModelProvider, ProviderRegistry
from kaiwen_agent.prompts import PromptRegistry
from kaiwen_agent.runtime import AgentFactory, RuntimeIdentity
from kaiwen_agent.standards import StandardsRegistry
from kaiwen_agent.tools.registry import ToolRegistry
from kaiwen_agent.types import ModelResponse


async def main() -> None:
    providers = ProviderRegistry()
    providers.register(
        "fake",
        lambda instructions: FakeModelProvider(
            [ModelResponse(text="Coding Kit control flow is ready.")]
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
    coding = CodingKitFactory(factory).create(CodingKitConfig(provider_ref="fake"))
    result = await coding.chat(
        "Explain the configured mode.",
        identity=RuntimeIdentity(session_id="coding-kit-example"),
    )
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
