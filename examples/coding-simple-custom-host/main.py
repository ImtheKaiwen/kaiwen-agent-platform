from __future__ import annotations

import asyncio
from pathlib import Path

from kaiwen_agent.agents import AgentDefinitionRegistry
from kaiwen_agent.capabilities import CapabilityRegistry
from kaiwen_agent.kits.coding import CodingKit
from kaiwen_agent.models import FakeModelProvider, ProviderRegistry
from kaiwen_agent.prompts import PromptRegistry
from kaiwen_agent.runtime import AgentFactory, RuntimeIdentity
from kaiwen_agent.standards import StandardsRegistry
from kaiwen_agent.tools import ToolRegistry
from kaiwen_agent.types import ModelResponse


async def main() -> None:
    providers = ProviderRegistry()
    providers.register(
        "host.fake",
        lambda _: FakeModelProvider([ModelResponse(text="Hosted identity accepted")]),
    )
    factory = AgentFactory(
        agents=AgentDefinitionRegistry(),
        prompts=PromptRegistry(),
        capabilities=CapabilityRegistry(),
        providers=providers,
        tools=ToolRegistry(),
        standards=StandardsRegistry(),
    )
    identity = RuntimeIdentity(
        session_id="authenticated-session",
        tenant_id="tenant-1",
        user_id="user-1",
        conversation_id="conversation-1",
    )
    kit = CodingKit.for_host(
        identity=identity,
        workspace=Path.cwd(),
        agent_factory=factory,
        provider_ref="host.fake",
    )
    print((await kit.agent().chat("Hello")).text)


if __name__ == "__main__":
    asyncio.run(main())
