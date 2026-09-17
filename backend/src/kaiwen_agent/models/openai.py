from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from kaiwen_agent.context import AgentContext
from kaiwen_agent.tools.definition import ToolDefinition
from kaiwen_agent.types import (
    AgentInput,
    ModelResponse,
    ModelUsage,
    ToolCall,
    ToolResult,
)


class OpenAIResponsesProvider:
    """OpenAI Responses API adapter with no shared conversation state."""

    def __init__(
        self,
        *,
        model: str,
        instructions: str | None = None,
        client: Any | None = None,
        store: bool = False,
        parallel_tool_calls: bool = True,
        output_schema: Mapping[str, Any] | None = None,
        output_name: str = "agent_output",
    ) -> None:
        if client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as error:
                raise RuntimeError(
                    "Install the OpenAI adapter with `pip install kaiwen-agent[openai]`."
                ) from error
            client = AsyncOpenAI()

        self._client = client
        self.model = model
        self.instructions = instructions
        self.store = store
        self.parallel_tool_calls = parallel_tool_calls
        self.output_schema = dict(output_schema) if output_schema is not None else None
        self.output_name = output_name

    async def respond(
        self,
        agent_input: AgentInput,
        *,
        context: AgentContext,
        tools: Sequence[ToolDefinition],
        tool_results: Sequence[ToolResult],
        previous_response_id: str | None,
    ) -> ModelResponse:
        provider_names = {
            self._provider_tool_name(definition.name): definition.name for definition in tools
        }
        if len(provider_names) != len(tools):
            raise ValueError("Tool names collide after OpenAI-compatible normalization")

        request: dict[str, Any] = {
            "model": self.model,
            "input": self._build_input(agent_input, tool_results, previous_response_id),
            "tools": [self._serialize_tool(definition) for definition in tools],
            "store": self.store,
            "parallel_tool_calls": self.parallel_tool_calls,
        }
        if self.instructions:
            request["instructions"] = self.instructions
        if previous_response_id:
            request["previous_response_id"] = previous_response_id
        if self.output_schema is not None:
            request["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": self.output_name,
                    "schema": self._strict_schema(self.output_schema),
                    "strict": True,
                }
            }
        safety_identifier = context.metadata.get("safety_identifier")
        if isinstance(safety_identifier, str) and safety_identifier:
            request["safety_identifier"] = safety_identifier

        response = await self._client.responses.create(**request)
        output_text = getattr(response, "output_text", None)
        structured_output: Any | None = None
        if self.output_schema is not None and output_text:
            structured_output = json.loads(output_text)

        calls: list[ToolCall] = []
        for item in getattr(response, "output", []):
            if getattr(item, "type", None) != "function_call":
                continue
            calls.append(
                ToolCall(
                    id=item.call_id,
                    name=provider_names.get(item.name, item.name),
                    arguments=json.loads(getattr(item, "arguments", "{}")),
                )
            )

        return ModelResponse(
            text=output_text,
            tool_calls=calls,
            provider_response_id=getattr(response, "id", None),
            structured_output=structured_output,
            usage=self._parse_usage(getattr(response, "usage", None)),
            model=getattr(response, "model", self.model),
        )

    @staticmethod
    def _build_input(
        agent_input: AgentInput,
        tool_results: Sequence[ToolResult],
        previous_response_id: str | None,
    ) -> str | list[dict[str, str]]:
        if previous_response_id:
            return [
                {
                    "type": "function_call_output",
                    "call_id": result.call_id,
                    "output": json.dumps(result.output, ensure_ascii=False, default=str),
                }
                for result in tool_results
            ]
        return agent_input.text

    @staticmethod
    def _serialize_tool(definition: ToolDefinition) -> dict[str, Any]:
        return {
            "type": "function",
            "name": OpenAIResponsesProvider._provider_tool_name(definition.name),
            "description": definition.description,
            "parameters": OpenAIResponsesProvider._strict_schema(definition.input_schema),
            "strict": True,
        }

    @staticmethod
    def _provider_tool_name(name: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_-]", "__", name)
        if not normalized or len(normalized) > 64:
            raise ValueError(f"Tool name cannot be represented for OpenAI: {name}")
        return normalized

    @staticmethod
    def _strict_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
        normalized = deepcopy(dict(schema))

        def visit(node: Any) -> None:
            if isinstance(node, dict):
                properties = node.get("properties")
                if node.get("type") == "object" and isinstance(properties, dict):
                    node["additionalProperties"] = False
                    node["required"] = list(properties)
                for value in node.values():
                    visit(value)
            elif isinstance(node, list):
                for value in node:
                    visit(value)

        visit(normalized)
        return normalized

    @staticmethod
    def _parse_usage(raw_usage: Any | None) -> ModelUsage | None:
        if raw_usage is None:
            return None
        return ModelUsage(
            input_tokens=getattr(raw_usage, "input_tokens", 0),
            output_tokens=getattr(raw_usage, "output_tokens", 0),
            total_tokens=getattr(raw_usage, "total_tokens", 0),
        )
