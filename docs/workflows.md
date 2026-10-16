# Autonomous workflows

`kaiwen-agent` exposes a bounded, single-agent workflow control plane. It composes
existing runtime services rather than creating another model loop or executor.

## Execution boundary

`WorkflowPlan` is untrusted input. `WorkflowCompiler` validates owner identity,
allowlisted workers, effective capabilities, resource keys, graph structure, limits,
and strict JSON task input before producing an existing `TaskGraph`. Only
`TaskScheduler` executes the resulting tasks and persists task state.

A `WorkflowRevisionPlanner` may propose a replacement plan after task or quality
failure. Every proposal passes through the same compiler. The planner cannot execute
tasks, grant permissions, alter the resolved standards, or declare completion.

## Completion and repair

`WorkflowController` evaluates the fixed `StandardResolution` through the existing
`CompletionGate`. Mandatory requirements need owner-scoped, current-input evidence;
an agent statement is not evidence. Repair and replan attempts are finite and stop on
repeated failure fingerprints, exhausted limits, approval requirements, invalid
configuration, or the workflow cycle limit.

Side-effecting workers must separately compose the durable U5 action-intent,
approval, permission, and idempotency pipeline. Workflow compilation does not grant
tool authority.

## Recovery scope

The runtime run and scheduled task records are durable when the host supplies durable
stores. Recovery occurs at explicit safe boundaries with at-least-once semantics;
the platform does not claim token-level model-stream resumption. Interrupted external
effects remain subject to U5 reconciliation and are never retried merely because a
workflow is resumed.

`AgentRuntime.run()` intentionally continues to reject `RunMode.WORKFLOW`. Hosts use
`WorkflowController` with a structured, validated plan until a stable planning input
contract can be added without changing the chat fast path or duplicating the model
loop.
