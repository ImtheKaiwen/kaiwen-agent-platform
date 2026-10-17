from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from kaiwen_agent.kits.coding import CodingKit


async def run(model: str) -> None:
    async with CodingKit.local(
        workspace=Path.cwd(),
        provider="ollama",
        model=model,
        data_locality="local_only",
    ) as kit:
        reply = await kit.agent().chat("Briefly describe this coding assistant.")
        print(reply.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Kaiwen Agent local Ollama chat")
    parser.add_argument("--model", required=True, help="An already installed Ollama model")
    arguments = parser.parse_args()
    asyncio.run(run(arguments.model))


if __name__ == "__main__":
    main()
