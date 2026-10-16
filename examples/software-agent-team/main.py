import asyncio
from typing import Any

from kaiwen_agent.agents import (
    AgentDefinition,
    AgentDefinitionRegistry,
    VersionedReference,
)
from kaiwen_agent.jobs import (
    JobContext,
    JobManager,
    SchedulerTaskRuntimeAdapter,
    SubagentDelegator,
)
from kaiwen_agent.policy import DelegationPolicy, PolicyEngine, PolicyRegistry
from kaiwen_agent.tasks import AgentTask
from kaiwen_agent.teams import (
    TeamDefinition,
    TeamDelegationRequest,
    TeamMemberDefinition,
    TeamRuntime,
)
from kaiwen_agent.workers import FunctionWorker, TaskExecutionContext, WorkerRegistry


def agent(agent_id: str, permissions: frozenset[str]) -> AgentDefinition:
    return AgentDefinition(
        id=agent_id,
        version=1,
        role=agent_id,
        instructions_ref=VersionedReference(id=f"{agent_id}-prompt", version=1),
        provider_ref="fake",
        capability_manifest_ref=VersionedReference(id=agent_id, version=1),
        permissions=permissions,
    )


async def main() -> None:
    async def review(task: AgentTask, context: TaskExecutionContext) -> dict[str, Any]:
        del task, context
        return {"summary": "Review complete", "evidence_refs": ["artifact://review-1"]}

    workers = WorkerRegistry()
    workers.register("reviewer", FunctionWorker(review))
    jobs = JobManager(
        runtime=SchedulerTaskRuntimeAdapter(workers=workers),
        allowed_worker_ids={"reviewer"},
    )
    runtime = TeamRuntime(
        definition=TeamDefinition(
            id="software",
            version=1,
            lead_agent_ref=VersionedReference(id="lead", version=1),
            members=(
                TeamMemberDefinition(
                    role="reviewer",
                    agent_ref=VersionedReference(id="reviewer", version=1),
                    capabilities=frozenset({"repo.read"}),
                ),
            ),
        ),
        agents=AgentDefinitionRegistry(
            [
                agent("lead", frozenset({"repo.read"})),
                agent("reviewer", frozenset({"repo.read"})),
            ]
        ),
        delegator=SubagentDelegator(
            jobs=jobs,
            policy_engine=PolicyEngine(
                registry=PolicyRegistry(
                    [
                        DelegationPolicy(
                            allowed_delegates={"reviewer"},
                            max_depth=1,
                            max_parallel_jobs=1,
                        )
                    ]
                )
            ),
        ),
        jobs=jobs,
    )
    context = JobContext(
        tenant_id="example",
        user_id="developer",
        session_id="quickstart",
        agent_id="lead",
        run_id="run-1",
        capabilities=frozenset({"repo.read"}),
    )
    reference = await runtime.delegate(
        context,
        TeamDelegationRequest(
            objective="Review the proposed change",
            requested_capabilities=frozenset({"repo.read"}),
        ),
    )
    handoff = await runtime.wait_handoff(context, reference.id)
    print(f"{handoff.role}: {handoff.summary}")


if __name__ == "__main__":
    asyncio.run(main())
