import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from kaiwen_agent.artifacts import ArtifactManager
from kaiwen_agent.control import RunControl
from kaiwen_agent.persistence import SQLitePersistence
from kaiwen_agent.quality import CompletionGate, VerifierRegistry
from kaiwen_agent.runtime import (
    AutonomyLevel,
    DurableRunManager,
    RuntimeIdentity,
    RuntimeVersionPins,
)
from kaiwen_agent.standards import StandardResolution
from kaiwen_agent.tasks import AgentTask, TaskScheduler
from kaiwen_agent.workers import FunctionWorker, TaskExecutionContext, WorkerRegistry
from kaiwen_agent.workflow import (
    WorkflowCompiler,
    WorkflowController,
    WorkflowPlan,
    WorkflowTaskSpec,
)


async def main() -> None:
    identity = RuntimeIdentity(
        session_id="quickstart",
        tenant_id="example",
        user_id="developer",
    )
    pins = RuntimeVersionPins(
        workspace_id="example",
        workspace_version=1,
        agent_id="builder",
        agent_version=1,
        prompt_id="provider-free",
        prompt_version=1,
        prompt_checksum="example",
        capability_manifest_id="builder",
        capability_manifest_version=1,
        provider_ref="fake",
        tool_names=(),
        toolset_checksum="example",
    )

    async def execute(task: AgentTask, context: TaskExecutionContext) -> dict[str, Any]:
        await context.checkpoint(state={"completed": task.name})
        return {"summary": f"Completed {task.name}"}

    with TemporaryDirectory() as directory:
        store = SQLitePersistence(Path(directory) / "workflow.sqlite3")
        runs = DurableRunManager(store)
        run = await runs.create(
            identity=identity,
            autonomy=AutonomyLevel.AUTONOMOUS,
            version_pins=pins,
        )
        workers = WorkerRegistry()
        workers.register("builder", FunctionWorker(execute))
        compiler = WorkflowCompiler(
            workers=workers,
            worker_allowlist=frozenset({"builder"}),
            effective_capabilities=frozenset({"workspace.read"}),
        )
        controller = WorkflowController(
            runs=runs,
            compiler=compiler,
            scheduler_factory=lambda graph: TaskScheduler(
                graph=graph,
                workers=workers,
                store=store,
                control=RunControl(checkpoints=store),
            ),
            completion_gate=CompletionGate(
                verifiers=VerifierRegistry(),
                artifacts=ArtifactManager(),
            ),
        )
        outcome = await controller.execute(
            run=run,
            identity=identity,
            plan=WorkflowPlan(
                objective="Inspect then summarize",
                tasks=(
                    WorkflowTaskSpec(
                        id="inspect",
                        name="Inspect",
                        worker_id="builder",
                        capabilities=frozenset({"workspace.read"}),
                    ),
                    WorkflowTaskSpec(
                        id="summarize",
                        name="Summarize",
                        worker_id="builder",
                        dependencies=("inspect",),
                    ),
                ),
            ),
            standards=StandardResolution(pack_refs=(), requirements=(), prompt_refs=()),
            protected_input_fingerprint="provider-free-example",
        )
        print(outcome.status.value)


if __name__ == "__main__":
    asyncio.run(main())
