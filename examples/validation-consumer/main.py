from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from kaiwen_agent.agents import VersionedReference
from kaiwen_agent.artifacts import (
    ArtifactContext,
    ArtifactCreate,
    ArtifactManager,
    ArtifactType,
)
from kaiwen_agent.control import RunControl
from kaiwen_agent.integrations import WorkspaceFilesystem
from kaiwen_agent.persistence import SQLitePersistence
from kaiwen_agent.quality import (
    CompletionGate,
    VerificationContext,
    VerificationResult,
    VerificationStatus,
    VerifierRegistry,
)
from kaiwen_agent.runtime import (
    AutonomyLevel,
    DurableRunManager,
    RuntimeIdentity,
    RuntimeVersionPins,
)
from kaiwen_agent.standards import (
    RequirementDefinition,
    RequirementObligation,
    RequirementSeverity,
    ResolvedRequirement,
    StandardsPack,
    StandardsRegistry,
    StandardsResolver,
)
from kaiwen_agent.tasks import AgentTask, TaskScheduler
from kaiwen_agent.workers import FunctionWorker, TaskExecutionContext, WorkerRegistry
from kaiwen_agent.workflow import (
    WorkflowCompiler,
    WorkflowController,
    WorkflowOutcomeStatus,
    WorkflowPlan,
    WorkflowTaskSpec,
)

FINGERPRINT = "todo-cli-validation-v1"


class TestVerifier:
    verifier_id = "python.tests"

    def __init__(self, evidence: list[str]) -> None:
        self.evidence = evidence

    async def verify(
        self,
        requirement: ResolvedRequirement,
        *,
        context: VerificationContext,
    ) -> VerificationResult:
        del requirement, context
        return VerificationResult(
            requirement_id="software.tests",
            status=VerificationStatus.PASS if self.evidence else VerificationStatus.FAIL,
            evidence_refs=tuple(self.evidence),
            verifier_id=self.verifier_id,
        )


def _write(filesystem: WorkspaceFilesystem, path: str, content: str) -> None:
    target = Path(path)
    (filesystem.roots["project"] / target.parent).mkdir(parents=True, exist_ok=True)
    filesystem.write_text("project", path, content)


async def validate(workspace: Path) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    filesystem = WorkspaceFilesystem(workspace_id="todo-validation", roots={"project": workspace})
    database = workspace / ".validation.sqlite3"
    store = SQLitePersistence(database)
    artifacts = ArtifactManager()
    evidence: list[str] = []
    identity = RuntimeIdentity(
        session_id="consumer-validation",
        tenant_id="validation",
        user_id="developer",
        conversation_id="todo-cli",
        trace_id="trace-consumer-validation",
    )
    runs = DurableRunManager(store)
    run = await runs.create(
        identity=identity,
        autonomy=AutonomyLevel.AUTONOMOUS,
        version_pins=RuntimeVersionPins(
            workspace_id="todo-validation",
            workspace_version=1,
            agent_id="todo-team",
            agent_version=1,
            prompt_id="deterministic-validation",
            prompt_version=1,
            prompt_checksum=FINGERPRINT,
            capability_manifest_id="todo-team",
            capability_manifest_version=1,
            provider_ref="provider-free",
            tool_names=(),
            toolset_checksum=FINGERPRINT,
        ),
    )

    async def planner(task: AgentTask, context: TaskExecutionContext) -> dict[str, Any]:
        del task
        _write(
            filesystem,
            "PLAN.md",
            "# Plan\n\n1. Implement JSON storage.\n2. Implement CLI.\n3. Test CRUD.\n",
        )
        await context.checkpoint(state={"phase": "planned"})
        return {"summary": "Plan written"}

    async def coder(task: AgentTask, context: TaskExecutionContext) -> dict[str, Any]:
        del task
        _write(filesystem, "todo_cli/__init__.py", "")
        _write(
            filesystem,
            "todo_cli/store.py",
            """from __future__ import annotations

import json
from pathlib import Path


class TodoStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def add(self, title: str) -> dict[str, object]:
        items = self.list()
        item = {"id": max((int(x["id"]) for x in items), default=0) + 1,
                "title": title, "done": False}
        items.append(item)
        self._save(items)
        return item

    def complete(self, item_id: int) -> None:
        items = self.list()
        for item in items:
            if item["id"] == item_id:
                item["done"] = True
                self._save(items)
                return
        raise KeyError(item_id)

    def delete(self, item_id: int) -> None:
        items = [item for item in self.list() if item["id"] != item_id]
        self._save(items)

    def _save(self, items: list[dict[str, object]]) -> None:
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")
""",
        )
        _write(
            filesystem,
            "todo_cli/cli.py",
            """from __future__ import annotations

import argparse
from pathlib import Path

from .store import TodoStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("add", "list", "complete", "delete"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--db", type=Path, default=Path("todos.json"))
    args = parser.parse_args()
    store = TodoStore(args.db)
    if args.command == "add":
        print(store.add(args.value or "Untitled"))
    elif args.command == "list":
        print(store.list())
    elif args.command == "complete":
        store.complete(int(args.value or "0"))
    else:
        store.delete(int(args.value or "0"))


if __name__ == "__main__":
    main()
""",
        )
        _write(
            filesystem,
            "README.md",
            '# Todo CLI\n\nRun `python -m todo_cli.cli add "Task"`.\n',
        )
        _write(
            filesystem,
            ".github/workflows/ci.yml",
            "name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n"
            "      - run: python -m unittest discover -s tests\n",
        )
        await context.checkpoint(state={"phase": "implemented"})
        return {"summary": "Application written"}

    async def tester(task: AgentTask, context: TaskExecutionContext) -> dict[str, Any]:
        del task
        _write(
            filesystem,
            "tests/test_store.py",
            """from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from todo_cli.store import TodoStore


class TodoStoreTests(TestCase):
    def test_crud(self) -> None:
        with TemporaryDirectory() as directory:
            store = TodoStore(Path(directory) / "todos.json")
            first = store.add("Ship")
            self.assertEqual(store.list(), [first])
            store.complete(int(first["id"]))
            self.assertTrue(store.list()[0]["done"])
            store.delete(int(first["id"]))
            self.assertEqual(store.list(), [])
""",
        )
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            cwd=workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        report = {
            "returncode": process.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }
        artifact = await artifacts.create(
            identity_artifact_context(identity, run.id),
            ArtifactCreate(
                type=ArtifactType.REPORT,
                mime_type="application/json",
                content=json.dumps(report, sort_keys=True).encode(),
                labels={
                    "evidence_type": "test_report",
                    "input_fingerprint": FINGERPRINT,
                },
            ),
        )
        evidence.append(artifact.id)
        if process.returncode:
            raise RuntimeError("Generated Todo CLI tests failed")
        await context.checkpoint(state={"phase": "tested", "returncode": 0})
        return {"summary": "Tests passed", "evidence_refs": [artifact.id]}

    async def reviewer(task: AgentTask, context: TaskExecutionContext) -> dict[str, Any]:
        del task
        required = (
            "PLAN.md",
            "README.md",
            "todo_cli/store.py",
            "todo_cli/cli.py",
            "tests/test_store.py",
            ".github/workflows/ci.yml",
        )
        missing = [path for path in required if not (workspace / path).is_file()]
        if missing:
            raise RuntimeError(f"Missing deliverables: {missing}")
        await context.checkpoint(state={"phase": "reviewed"})
        return {"summary": "Deliverables verified"}

    workers = WorkerRegistry()
    workers.register("planner", FunctionWorker(planner))
    workers.register("coder", FunctionWorker(coder))
    workers.register("tester", FunctionWorker(tester))
    workers.register("reviewer", FunctionWorker(reviewer))
    standards = StandardsResolver(
        StandardsRegistry(
            [
                StandardsPack(
                    id="software-validation",
                    version=1,
                    requirements=(
                        RequirementDefinition(
                            id="software.tests",
                            description="Generated application tests must pass",
                            obligation=RequirementObligation.MUST,
                            severity=RequirementSeverity.ERROR,
                            acceptance_criteria=("Unit test command exits successfully",),
                            verifier_ref="python.tests",
                            evidence_types=frozenset({"test_report"}),
                        ),
                    ),
                )
            ]
        )
    ).resolve([VersionedReference(id="software-validation", version=1)])
    verifiers = VerifierRegistry()
    verifiers.register(TestVerifier(evidence))
    controller = WorkflowController(
        runs=runs,
        compiler=WorkflowCompiler(
            workers=workers,
            worker_allowlist=frozenset({"planner", "coder", "tester", "reviewer"}),
            effective_capabilities=frozenset({"workspace.read", "workspace.write", "tests.run"}),
        ),
        scheduler_factory=lambda graph: TaskScheduler(
            graph=graph,
            workers=workers,
            store=store,
            control=RunControl(checkpoints=store),
            max_concurrency=2,
        ),
        completion_gate=CompletionGate(verifiers=verifiers, artifacts=artifacts),
    )
    outcome = await controller.execute(
        run=run,
        identity=identity,
        plan=WorkflowPlan(
            objective="Build and verify a modular Python Todo CLI",
            tasks=(
                WorkflowTaskSpec(id="plan", name="Plan", worker_id="planner"),
                WorkflowTaskSpec(
                    id="code",
                    name="Implement",
                    worker_id="coder",
                    dependencies=("plan",),
                    capabilities=frozenset({"workspace.write"}),
                ),
                WorkflowTaskSpec(
                    id="test",
                    name="Test",
                    worker_id="tester",
                    dependencies=("code",),
                    capabilities=frozenset({"tests.run"}),
                ),
                WorkflowTaskSpec(
                    id="review",
                    name="Review",
                    worker_id="reviewer",
                    dependencies=("test",),
                    capabilities=frozenset({"workspace.read"}),
                ),
            ),
        ),
        standards=standards,
        protected_input_fingerprint=FINGERPRINT,
    )
    if outcome.status != WorkflowOutcomeStatus.COMPLETED:
        raise RuntimeError(f"Validation workflow failed: {outcome.status.value}")
    return {
        "status": outcome.status.value,
        "tasks": [task.metadata["logical_task_id"] for task in outcome.tasks],
        "quality": outcome.quality_result.status.value if outcome.quality_result else None,
        "workspace": str(workspace),
    }


def identity_artifact_context(identity: RuntimeIdentity, run_id: str) -> ArtifactContext:
    return ArtifactContext(
        tenant_id=identity.tenant_id or "validation",
        user_id=identity.user_id or "developer",
        session_id=identity.session_id,
        trace_id=identity.trace_id or "trace-consumer-validation",
        run_id=run_id,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(validate(args.workspace.resolve())), sort_keys=True))


if __name__ == "__main__":
    main()
