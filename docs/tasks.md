# Durable task execution

The task runtime separates planning from execution. A planner may produce tasks and
dependencies, but only `TaskScheduler` changes execution state.

## Components

- `AgentTask`: durable input, output, progress, retry, resource, and lifecycle state.
- `TaskGraph`: dependency validation, cycle rejection, and deterministic ordering.
- `TaskScheduler`: concurrency, dependencies, retry, cancellation, and events.
- `WorkerRegistry`: maps stable agent IDs to stateless worker implementations.
- `ResourceManager`: atomically acquires all resources required by a task.
- `RunControl`: mailbox plus durable safe checkpoints.

## Control contract

Workers remain cooperative and call `context.checkpoint()` after logical steps.
Cancellation and pause are applied at those safe boundaries. New instructions are
returned from the checkpoint and never injected into arbitrary running code.

```python
messages = await context.checkpoint(state={"last_file": filename})
for message in messages:
    if message.type == "instruction":
        apply_instruction(message.content)
```

Checkpoints are written before pending control messages are applied. If cancellation
arrives, the latest resumable state therefore remains available.

## Resource and concurrency rules

Dependencies must be completed before a task becomes ready. Independent ready tasks
may execute concurrently up to the global and per-agent limits. Resource keys are
acquired as one atomic set, preventing partial-lock deadlocks. Capacity defaults to
one unless configured otherwise.

## Retry rules

Workers raise `RetryableTaskError` with a stable error code. A task retries only when
that code appears in its `TaskRetryPolicy.retry_on` set and attempts remain. Generic
exceptions are terminal by default. Timeout uses the stable `timeout` code.

Run `examples/task-graph/main.py` for a provider-free example.
