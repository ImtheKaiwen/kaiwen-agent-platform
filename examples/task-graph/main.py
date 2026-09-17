import asyncio

from kaiwen_agent.tasks import AgentTask, TaskGraph, TaskScheduler
from kaiwen_agent.workers import FunctionWorker, WorkerRegistry


async def execute(task, context):
    await context.checkpoint(state={"phase": "started"})
    await context.report_progress(0.5, details={"message": f"{task.name} is running"})
    await asyncio.sleep(0.05)
    return {"completed": task.name}


async def main() -> None:
    inspect = AgentTask(id="inspect", name="Inspect files", agent_id="local")
    upload = AgentTask(
        id="upload",
        name="Upload",
        agent_id="cloud",
        dependencies=["inspect"],
        resource_keys=["deployment-slot"],
    )
    summarize = AgentTask(
        id="summarize",
        name="Create summary",
        agent_id="local",
        dependencies=["inspect"],
    )

    workers = WorkerRegistry()
    workers.register("local", FunctionWorker(execute))
    workers.register("cloud", FunctionWorker(execute))
    scheduler = TaskScheduler(
        graph=TaskGraph([inspect, upload, summarize]),
        workers=workers,
        max_concurrency=2,
    )
    tasks = await scheduler.run()
    for task in tasks:
        print(f"{task.id}: {task.status} ({task.attempts} attempt)")


if __name__ == "__main__":
    asyncio.run(main())
