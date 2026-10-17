from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any

from kaiwen_agent.artifacts import ArtifactManager
from kaiwen_agent.context import AgentContext
from kaiwen_agent.control import RunControl
from kaiwen_agent.kits.coding import (
    CodingExecutionBinding,
    CodingKit,
    ObjectivePlanner,
    PlanningConstraints,
)
from kaiwen_agent.models import ModelCapabilities, ModelToolStrategy
from kaiwen_agent.persistence import SQLitePersistence
from kaiwen_agent.quality import CompletionGate, VerifierRegistry
from kaiwen_agent.runtime import DurableRunManager
from kaiwen_agent.standards import StandardResolution, StandardsRegistry
from kaiwen_agent.tasks import AgentTask, TaskScheduler
from kaiwen_agent.tools.definition import ToolDefinition
from kaiwen_agent.types import AgentInput, ModelResponse, ToolResult
from kaiwen_agent.workers import FunctionWorker, TaskExecutionContext, WorkerRegistry
from kaiwen_agent.workflow import WorkflowCompiler, WorkflowController


class DeterministicPlanner:
    async def propose_plan(
        self, *, objective: str, context: dict[str, Any], correction: str | None
    ) -> dict[str, Any]:
        del context, correction
        return {
            "objective": objective,
            "tasks": [{"id": "verify", "name": "Verify", "worker_id": "worker"}],
        }


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="kaiwen-simple-agent-") as directory:
        workspace = Path(directory)
        store = SQLitePersistence(workspace / "runtime.sqlite3")
        runs = DurableRunManager(store)
        workers = WorkerRegistry()

        async def execute(task: AgentTask, context: TaskExecutionContext) -> dict[str, Any]:
            await context.checkpoint(state={"task": task.id, "verified": True})
            return {"verified": True}

        workers.register("worker", FunctionWorker(execute))
        controller = WorkflowController(
            runs=runs,
            compiler=WorkflowCompiler(
                workers=workers,
                worker_allowlist=frozenset({"worker"}),
                effective_capabilities=frozenset(),
                resource_allowlist=frozenset(),
            ),
            scheduler_factory=lambda graph: TaskScheduler(
                graph=graph,
                workers=workers,
                store=store,
                control=RunControl(checkpoints=store),
            ),
            completion_gate=CompletionGate(
                verifiers=VerifierRegistry(), artifacts=ArtifactManager()
            ),
        )
        execution = CodingExecutionBinding(
            planner=ObjectivePlanner(
                DeterministicPlanner(),
                constraints=PlanningConstraints(worker_allowlist=frozenset({"worker"})),
            ),
            controller=controller,
            runs=runs,
            standards=StandardResolution(pack_refs=(), requirements=(), prompt_refs=()),
            standards_registry=StandardsRegistry(),
            protected_input_fingerprint=lambda objective: sha256(objective.encode()).hexdigest(),
        )
        capabilities = ModelCapabilities(
            provider="fake",
            model="deterministic",
            context_window=8_192,
            tool_strategy=ModelToolStrategy.NATIVE,
            structured_output=True,
        )

        async with CodingKit.local(
            workspace=workspace,
            provider="fake",
            model="deterministic",
            provider_factory=lambda _: _UnusedProvider(),
            model_capabilities=capabilities,
            execution=execution,
        ) as kit:
            handle = await kit.agent().start("Run a bounded verified task")
            result = await handle.wait(timeout=5)
            print(result.status, result.tasks_completed)


class _UnusedProvider:
    async def respond(
        self,
        agent_input: AgentInput,
        *,
        context: AgentContext,
        tools: Sequence[ToolDefinition],
        tool_results: Sequence[ToolResult],
        provider_state: Any | None,
    ) -> ModelResponse:
        del agent_input, context, tools, tool_results, provider_state
        raise AssertionError("The deterministic workflow should not invoke chat")


if __name__ == "__main__":
    asyncio.run(main())
