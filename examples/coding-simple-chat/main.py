from __future__ import annotations

import asyncio
from pathlib import Path

from kaiwen_agent.kits.coding import CodingKit
from kaiwen_agent.models import FakeModelProvider
from kaiwen_agent.types import ModelResponse


async def main() -> None:
    provider_created = False

    def provider_factory(instructions: str) -> FakeModelProvider:
        nonlocal provider_created
        provider_created = True
        assert instructions
        return FakeModelProvider([ModelResponse(text="Merhaba! Araçsız sohbet hazır.")])

    async with CodingKit.local(
        workspace=Path.cwd(),
        provider="fake",
        model="deterministic",
        provider_factory=provider_factory,
        user_language="tr",
    ) as kit:
        assert not provider_created
        reply = await kit.agent().chat("Türkçe yanıt ver.")
        print(reply.text)


if __name__ == "__main__":
    asyncio.run(main())
