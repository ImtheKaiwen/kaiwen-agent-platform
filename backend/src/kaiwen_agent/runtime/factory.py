from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from kaiwen_agent.agents import (
    AgentDefinition,
    AgentDefinitionRegistry,
    VersionedReference,
)
from kaiwen_agent.capabilities import CapabilityManifest, CapabilityRegistry
from kaiwen_agent.events import EventSink
from kaiwen_agent.exceptions import ToolNotFoundError
from kaiwen_agent.models import ProviderRegistry
from kaiwen_agent.prompts import PromptDefinition, PromptRegistry
from kaiwen_agent.runtime.agent_runtime import AgentRuntime
from kaiwen_agent.runtime.profile import RuntimeVersionPins, WorkspaceProfile
from kaiwen_agent.sessions import RunStore
from kaiwen_agent.tools.definition import ToolDefinition
from kaiwen_agent.tools.execution import ToolExecutor
from kaiwen_agent.tools.registry import ToolRegistry


class RuntimeCompositionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ConfiguredAgentRuntime:
    runtime: AgentRuntime
    definition: AgentDefinition
    profile: WorkspaceProfile
    prompt: PromptDefinition
    capability_manifest: CapabilityManifest
    pins: RuntimeVersionPins


class AgentFactory:
    """Validates registries and composes an AgentRuntime without a second loop."""

    def __init__(
        self,
        *,
        agents: AgentDefinitionRegistry,
        prompts: PromptRegistry,
        capabilities: CapabilityRegistry,
        providers: ProviderRegistry,
        tools: ToolRegistry,
        event_sink: EventSink | None = None,
        run_store: RunStore | None = None,
        tool_executor: ToolExecutor | None = None,
        services: Mapping[str, Any] | None = None,
    ) -> None:
        self.agents = agents
        self.prompts = prompts
        self.capabilities = capabilities
        self.providers = providers
        self.tools = tools
        self.event_sink = event_sink
        self.run_store = run_store
        self.tool_executor = tool_executor
        self.services = dict(services or {})

    def create(
        self,
        profile: WorkspaceProfile,
        *,
        agent_ref: VersionedReference | None = None,
    ) -> ConfiguredAgentRuntime:
        reference = agent_ref or profile.default_agent_ref
        self._require_profile_agent(profile, reference)
        definition = self._resolve_definition(reference)
        prompt = self._resolve_prompt(definition)
        manifest = self._resolve_manifest(definition)
        selected_tools = self._resolve_tools(profile, definition)
        if definition.provider_ref not in profile.provider_allowlist:
            raise RuntimeCompositionError(
                f"Provider is not allowed by workspace profile: {definition.provider_ref}"
            )
        try:
            model = self.providers.create(definition.provider_ref, instructions=prompt.template)
        except KeyError as error:
            raise RuntimeCompositionError(str(error)) from error

        pins = self._pins(profile, definition, prompt, manifest, selected_tools)
        runtime = AgentRuntime(
            name=definition.id,
            model=model,
            tools=selected_tools,
            permissions=definition.permissions,
            event_sink=self.event_sink,
            run_store=self.run_store,
            tool_executor=self.tool_executor,
            services=self.services,
            default_autonomy=profile.default_autonomy,
            max_steps=definition.max_steps,
            metadata={
                "agent_role": definition.role,
                "memory_namespaces": sorted(definition.memory_namespaces),
                "runtime_version_pins": pins.model_dump(mode="json"),
            },
        )
        return ConfiguredAgentRuntime(
            runtime=runtime,
            definition=definition,
            profile=profile,
            prompt=prompt,
            capability_manifest=manifest,
            pins=pins,
        )

    @staticmethod
    def _require_profile_agent(profile: WorkspaceProfile, reference: VersionedReference) -> None:
        if reference not in profile.agent_refs:
            raise RuntimeCompositionError(
                f"Agent is not allowed by workspace profile: {reference.id}@{reference.version}"
            )

    def _resolve_definition(self, reference: VersionedReference) -> AgentDefinition:
        try:
            return self.agents.resolve(reference)
        except KeyError as error:
            raise RuntimeCompositionError(str(error)) from error

    def _resolve_prompt(self, definition: AgentDefinition) -> PromptDefinition:
        reference = definition.instructions_ref
        try:
            prompt = self.prompts.get(reference.id, reference.version)
        except KeyError as error:
            raise RuntimeCompositionError(str(error)) from error
        if prompt.variables:
            raise RuntimeCompositionError(
                "Agent instruction prompts must not require runtime template variables"
            )
        return prompt

    def _resolve_manifest(self, definition: AgentDefinition) -> CapabilityManifest:
        reference = definition.capability_manifest_ref
        try:
            manifest = self.capabilities.get(reference.id, reference.version)
        except KeyError as error:
            raise RuntimeCompositionError(str(error)) from error
        if manifest.agent_id != definition.id:
            raise RuntimeCompositionError("Capability manifest must belong to the agent definition")
        if not definition.tool_refs <= manifest.tools:
            raise RuntimeCompositionError("Agent tools exceed its capability manifest")
        if not definition.memory_namespaces <= manifest.memory_namespaces:
            raise RuntimeCompositionError("Agent memory scopes exceed its capability manifest")
        return manifest

    def _resolve_tools(
        self,
        profile: WorkspaceProfile,
        definition: AgentDefinition,
    ) -> tuple[ToolDefinition, ...]:
        if not definition.tool_refs <= profile.tool_allowlist:
            raise RuntimeCompositionError("Agent tools exceed the workspace tool allowlist")
        selected: list[ToolDefinition] = []
        for name in sorted(definition.tool_refs):
            try:
                tool = self.tools.get(name)
            except ToolNotFoundError as error:
                raise RuntimeCompositionError(str(error)) from error
            if not tool.permissions <= definition.permissions:
                raise RuntimeCompositionError(
                    f"Agent permissions cannot execute configured tool: {name}"
                )
            selected.append(tool)
        return tuple(selected)

    @staticmethod
    def _pins(
        profile: WorkspaceProfile,
        definition: AgentDefinition,
        prompt: PromptDefinition,
        manifest: CapabilityManifest,
        tools: tuple[ToolDefinition, ...],
    ) -> RuntimeVersionPins:
        tool_records = [
            {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.input_schema,
                "permissions": sorted(tool.permissions),
                "side_effect": tool.side_effect,
                "requires_approval": tool.requires_approval,
            }
            for tool in tools
        ]
        return RuntimeVersionPins(
            workspace_id=profile.id,
            workspace_version=profile.version,
            agent_id=definition.id,
            agent_version=definition.version,
            prompt_id=prompt.id,
            prompt_version=prompt.version,
            prompt_checksum=prompt.checksum,
            capability_manifest_id=manifest.agent_id,
            capability_manifest_version=manifest.version,
            provider_ref=definition.provider_ref,
            tool_names=tuple(tool.name for tool in tools),
            toolset_checksum=RuntimeVersionPins.toolset_hash(tool_records),
        )
