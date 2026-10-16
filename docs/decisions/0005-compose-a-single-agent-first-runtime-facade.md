# ADR 0005: Compose a single-agent-first runtime facade

- Status: Accepted

## Context

The package has a synchronous-in-scope `Agent` loop, durable task execution,
background jobs, lifecycle wakeups, policy, context, memory, budgets, and registries.
Applications need one entry point that wires these capabilities without forcing a
simple conversation through a scheduler, evaluator, or agent team. Building another
model loop or executor would split authorization, recovery, and event semantics.

## Decision

Add an `AgentRuntime` as a composition facade over the existing `Agent`,
`ToolExecutor`, `TaskScheduler`, `JobManager`, `ContextBuilder`, `PolicyEngine`, and
registries. Preserve the existing `Agent` API and `ModelProvider.respond()` contract.

Execution mode and autonomy are independent axes:

- mode: `chat`, `action`, or `workflow`;
- autonomy: `manual`, `supervised`, or `autonomous`.

Chat is the fast path and does not instantiate task, team, or quality machinery.
Workflow planning compiles into the existing `TaskGraph`; only `TaskScheduler`
changes durable task execution state. Team orchestration is optional composition over
isolated single-agent runtime instances and is never required by the single-agent API.

## Consequences

- New features enter through injected ports and registries rather than a second core.
- Existing consumers can keep using `Agent` unchanged.
- Intent or mode selection never grants authority; policy and tool execution remain
  server-side and deny by default.
- Full autonomous side effects cannot be enabled until durable action intent,
  approval, idempotency, and recovery contracts are composed.
