from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from kaiwen_agent.agent import Agent
from kaiwen_agent.events import EventSink, InMemoryEventSink
from kaiwen_agent.models.base import ModelProvider
from kaiwen_agent.runtime.models import AutonomyLevel, RunMode, RuntimeIdentity
from kaiwen_agent.sessions import InMemoryRunStore, RunStore
from kaiwen_agent.tools.definition import ToolDefinition
from kaiwen_agent.tools.execution import ToolExecutor
from kaiwen_agent.tools.registry import ToolRegistry
from kaiwen_agent.types import AgentInput, AgentResult


class RuntimeModeUnavailableError(RuntimeError):
    pass


class AgentRuntime:
    """Single-agent-first composition facade over the existing Agent loop."""

    def __init__(
        self,
        *,
        name: str,
        model: ModelProvider,
        tools: Sequence[ToolDefinition] = (),
        permissions: set[str] | frozenset[str] | None = None,
        event_sink: EventSink | None = None,
        run_store: RunStore | None = None,
        tool_executor: ToolExecutor | None = None,
        services: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        default_autonomy: AutonomyLevel = AutonomyLevel.SUPERVISED,
        max_steps: int = 8,
    ) -> None:
        if not name:
            raise ValueError("name must not be empty")
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.name = name
        self.model = model
        self.registry = ToolRegistry(tools)
        self.permissions = frozenset(permissions or ())
        self.event_sink = event_sink or InMemoryEventSink()
        self.run_store = run_store or InMemoryRunStore()
        self.tool_executor = tool_executor or ToolExecutor()
        self.services = dict(services or {})
        self.metadata = dict(metadata or {})
        self.default_autonomy = default_autonomy
        self.max_steps = max_steps

    async def run(
        self,
        agent_input: AgentInput | str,
        *,
        identity: RuntimeIdentity,
        mode: RunMode = RunMode.CHAT,
        autonomy: AutonomyLevel | None = None,
        tool_names: Sequence[str] = (),
        services: Mapping[str, Any] | None = None,
    ) -> AgentResult:
        if mode == RunMode.WORKFLOW:
            raise RuntimeModeUnavailableError(
                "Workflow mode requires the durable workflow controller"
            )
        selected_tools = self._select_tools(tool_names) if mode == RunMode.ACTION else ()
        if mode == RunMode.CHAT and tool_names:
            raise ValueError("Chat mode does not expose tools; use action mode explicitly")
        effective_autonomy = autonomy or self.default_autonomy
        effective_services = {**self.services, **dict(services or {})}
        effective_identity = identity.model_copy(
            update={"metadata": {**identity.metadata, **self.metadata}}
        )
        context = effective_identity.to_agent_context(
            agent_id=self.name,
            services=effective_services,
            mode=mode,
            autonomy=effective_autonomy,
        )
        agent = Agent(
            name=self.name,
            model=self.model,
            tools=list(selected_tools),
            permissions=self.permissions,
            event_sink=self.event_sink,
            run_store=self.run_store,
            tool_executor=self.tool_executor,
            max_steps=self.max_steps,
        )
        return await agent.run(
            agent_input if isinstance(agent_input, AgentInput) else AgentInput(text=agent_input),
            context=context,
        )

    async def chat(
        self,
        text: str,
        *,
        identity: RuntimeIdentity,
        autonomy: AutonomyLevel | None = None,
        services: Mapping[str, Any] | None = None,
    ) -> AgentResult:
        return await self.run(
            text,
            identity=identity,
            mode=RunMode.CHAT,
            autonomy=autonomy,
            services=services,
        )

    async def action(
        self,
        text: str,
        *,
        identity: RuntimeIdentity,
        tool_names: Sequence[str],
        autonomy: AutonomyLevel | None = None,
        services: Mapping[str, Any] | None = None,
    ) -> AgentResult:
        return await self.run(
            text,
            identity=identity,
            mode=RunMode.ACTION,
            autonomy=autonomy,
            tool_names=tool_names,
            services=services,
        )

    def _select_tools(self, tool_names: Sequence[str]) -> tuple[ToolDefinition, ...]:
        if len(tool_names) != len(set(tool_names)):
            raise ValueError("tool_names must not contain duplicates")
        return tuple(self.registry.get(name) for name in tool_names)
