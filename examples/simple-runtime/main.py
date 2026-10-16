import asyncio

from kaiwen_agent import AgentRuntime, RuntimeIdentity
from kaiwen_agent.models.fake import FakeModelProvider
from kaiwen_agent.types import ModelResponse


async def main() -> None:
    runtime = AgentRuntime(
        name="quickstart",
        model=FakeModelProvider([ModelResponse(text="Hello from Kaiwen Agent.")]),
    )
    result = await runtime.chat("Hello", identity=RuntimeIdentity(session_id="quickstart"))
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
