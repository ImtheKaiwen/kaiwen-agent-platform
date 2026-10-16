import asyncio

import pytest
from pydantic import BaseModel

from kaiwen_agent import Agent, AgentContext, tool
from kaiwen_agent.events import InMemoryEventSink
from kaiwen_agent.exceptions import PermissionDeniedError
from kaiwen_agent.models.fake import FakeModelProvider
from kaiwen_agent.types import AgentInput, ModelResponse, ModelUsage, ToolCall


class GreetingInput(BaseModel):
    name: str


@tool(
    name="greeting.create",
    description="Create a greeting",
    input_model=GreetingInput,
    permissions={"greeting.read"},
)
async def create_greeting(context: AgentContext, arguments: GreetingInput) -> dict[str, str]:
    del context
    return {"message": f"Merhaba {arguments.name}"}


def test_agent_executes_tool_and_completes() -> None:
    events = InMemoryEventSink()
    provider = FakeModelProvider(
        [
            ModelResponse(
                tool_calls=[
                    ToolCall(id="call_1", name="greeting.create", arguments={"name": "Kaiwen"})
                ]
            ),
            ModelResponse(text="Selamlama hazır."),
        ]
    )
    agent = Agent(
        name="example",
        model=provider,
        tools=[create_greeting],
        permissions={"greeting.read"},
        event_sink=events,
    )

    result = asyncio.run(
        agent.run(
            AgentInput(text="Beni selamla"),
            context=AgentContext(session_id="session_1", permissions=frozenset({"greeting.read"})),
        )
    )

    assert result.status == "completed"
    assert result.text == "Selamlama hazır."
    assert result.tool_results[0].output == {"message": "Merhaba Kaiwen"}
    assert [event.type for event in events.events] == [
        "run.started",
        "policy.allowed",
        "policy.allowed",
        "tool.started",
        "tool.completed",
        "run.completed",
    ]


def test_permissions_are_intersection_of_agent_and_context() -> None:
    provider = FakeModelProvider(
        [
            ModelResponse(
                tool_calls=[
                    ToolCall(id="call_1", name="greeting.create", arguments={"name": "Kaiwen"})
                ]
            )
        ]
    )
    agent = Agent(
        name="example",
        model=provider,
        tools=[create_greeting],
        permissions={"greeting.read"},
    )

    with pytest.raises(PermissionDeniedError):
        asyncio.run(
            agent.run(
                AgentInput(text="Beni selamla"),
                context=AgentContext(session_id="session_1"),
            )
        )


def test_model_usage_is_accumulated_and_emitted() -> None:
    events = InMemoryEventSink()
    agent = Agent(
        name="usage-test",
        model=FakeModelProvider(
            [
                ModelResponse(
                    text="Tamam.",
                    model="test-model",
                    usage=ModelUsage(input_tokens=8, output_tokens=3, total_tokens=11),
                )
            ]
        ),
        event_sink=events,
    )

    result = asyncio.run(
        agent.run(
            AgentInput(text="Test"),
            context=AgentContext(session_id="session_1"),
        )
    )

    assert result.usage.total_tokens == 11
    usage_event = next(event for event in events.events if event.type == "run.status")
    assert usage_event.payload["kind"] == "model_usage"
    assert usage_event.payload["model"] == "test-model"


def test_agent_preserves_trusted_identity_in_effective_context() -> None:
    captured: AgentContext | None = None

    @tool(
        name="context.inspect",
        description="Inspect context",
        input_model=GreetingInput,
        permissions={"context.read"},
    )
    async def inspect_context(context: AgentContext, arguments: GreetingInput) -> dict[str, str]:
        nonlocal captured
        del arguments
        captured = context
        return {"ok": "true"}

    agent = Agent(
        name="admin-agent",
        model=FakeModelProvider(
            [
                ModelResponse(
                    tool_calls=[
                        ToolCall(
                            id="call_1",
                            name="context.inspect",
                            arguments={"name": "ignored"},
                        )
                    ]
                ),
                ModelResponse(text="Done"),
            ]
        ),
        tools=[inspect_context],
        permissions={"context.read"},
    )
    asyncio.run(
        agent.run(
            AgentInput(text="Inspect"),
            context=AgentContext(
                session_id="session_1",
                tenant_id="tenant_1",
                user_id="user_1",
                conversation_id="conversation_1",
                client_id="client_1",
                environment="production",
                permissions=frozenset({"context.read"}),
            ),
        )
    )
    assert captured is not None
    assert captured.agent_id == "admin-agent"
    assert captured.tenant_id == "tenant_1"
    assert captured.user_id == "user_1"
    assert captured.conversation_id == "conversation_1"
    assert captured.client_id == "client_1"
    assert captured.environment == "production"
