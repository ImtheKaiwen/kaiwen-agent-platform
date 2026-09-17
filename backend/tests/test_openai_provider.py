import asyncio
import json
from types import SimpleNamespace
from typing import Any

from kaiwen_agent import Agent, AgentContext
from kaiwen_agent.models.openai import OpenAIResponsesProvider
from kaiwen_agent.types import AgentInput, ToolResult

from .test_agent import create_greeting


class FakeResponsesResource:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    async def create(self, **request: Any) -> Any:
        self.requests.append(request)
        return self.responses.pop(0)


def make_client(responses: list[Any]) -> Any:
    return SimpleNamespace(responses=FakeResponsesResource(responses))


def test_openai_provider_serializes_and_parses_function_calls() -> None:
    client = make_client(
        [
            SimpleNamespace(
                id="resp_1",
                model="test-model",
                output_text="",
                output=[
                    SimpleNamespace(
                        type="function_call",
                        call_id="call_1",
                        name="greeting__create",
                        arguments='{"name":"Kaiwen"}',
                    )
                ],
                usage=SimpleNamespace(input_tokens=10, output_tokens=4, total_tokens=14),
            )
        ]
    )
    provider = OpenAIResponsesProvider(model="test-model", client=client)

    response = asyncio.run(
        provider.respond(
            AgentInput(text="Selamla"),
            context=AgentContext(
                session_id="session_1",
                metadata={"safety_identifier": "hashed-user"},
            ),
            tools=[create_greeting],
            tool_results=[],
            previous_response_id=None,
        )
    )

    request = client.responses.requests[0]
    assert request["input"] == "Selamla"
    assert request["store"] is False
    assert request["safety_identifier"] == "hashed-user"
    assert request["tools"][0]["strict"] is True
    assert request["tools"][0]["name"] == "greeting__create"
    assert request["tools"][0]["parameters"]["additionalProperties"] is False
    assert request["tools"][0]["parameters"]["required"] == ["name"]
    assert response.provider_response_id == "resp_1"
    assert response.tool_calls[0].arguments == {"name": "Kaiwen"}
    assert response.usage is not None
    assert response.usage.total_tokens == 14


def test_openai_provider_submits_tool_outputs_to_previous_response() -> None:
    client = make_client(
        [
            SimpleNamespace(
                id="resp_2",
                model="test-model",
                output_text='{"answer":"tamam"}',
                output=[],
                usage=None,
            )
        ]
    )
    provider = OpenAIResponsesProvider(
        model="test-model",
        client=client,
        output_schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    )

    response = asyncio.run(
        provider.respond(
            AgentInput(text="ignored on continuation"),
            context=AgentContext(session_id="session_1"),
            tools=[],
            tool_results=[
                ToolResult(call_id="call_1", name="greeting.create", output={"ok": True})
            ],
            previous_response_id="resp_1",
        )
    )

    request = client.responses.requests[0]
    assert request["previous_response_id"] == "resp_1"
    assert request["input"][0]["type"] == "function_call_output"
    assert json.loads(request["input"][0]["output"]) == {"ok": True}
    assert request["text"]["format"]["type"] == "json_schema"
    assert response.structured_output == {"answer": "tamam"}


def test_same_agent_core_runs_with_openai_adapter() -> None:
    client = make_client(
        [
            SimpleNamespace(
                id="resp_1",
                model="test-model",
                output_text="",
                output=[
                    SimpleNamespace(
                        type="function_call",
                        call_id="call_1",
                        name="greeting__create",
                        arguments='{"name":"Kaiwen"}',
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                id="resp_2",
                model="test-model",
                output_text="Selamlama hazır.",
                output=[],
                usage=None,
            ),
        ]
    )
    agent = Agent(
        name="openai-contract-test",
        model=OpenAIResponsesProvider(model="test-model", client=client),
        tools=[create_greeting],
        permissions={"greeting.read"},
    )

    result = asyncio.run(
        agent.run(
            AgentInput(text="Beni selamla"),
            context=AgentContext(
                session_id="session_1",
                permissions=frozenset({"greeting.read"}),
            ),
        )
    )

    assert result.text == "Selamlama hazır."
    assert client.responses.requests[1]["previous_response_id"] == "resp_1"
