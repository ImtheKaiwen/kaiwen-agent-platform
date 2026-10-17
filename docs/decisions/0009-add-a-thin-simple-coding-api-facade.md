# ADR 0009: Add a thin Simple Coding API facade

- Status: Accepted

## Context

The opt-in Coding Kit exposes secure low-level composition through
`CodingKitFactory`, `CodingTeamFactory`, `ObjectivePlanner`, and the durable workflow
components. A consumer still needs substantial registry and lifecycle wiring for
common chat and coding workflows. Requiring that wiring in every consumer encourages
inconsistent security composition, while changing the existing constructors would
break the published `0.6.0a1` API.

## Decision

Add an opt-in `CodingKit` facade under `kaiwen_agent.kits.coding`. The facade is a
composition and lifecycle adapter only:

- chat delegates to the existing `CodingKitFactory` and `AgentRuntime` fast path;
- explicit actions delegate to the existing central `ToolExecutor` with an exact
  trusted allowlist;
- autonomous work delegates to `ObjectivePlanner`, `WorkflowController`,
  `TaskScheduler`, `CompletionGate`, and durable run stores;
- optional team work requires an explicit adapter backed by the existing
  `CodingTeamFactory` and `TeamRuntime`;
- run handles project owner-scoped durable state and canonical events rather than
  becoming another state store or executor.

Local mode is explicitly single-user and never substitutes for hosted
authentication. Merely supplying a workspace path grants no tools. Workflow and
side-effecting action paths fail closed unless the host supplies compatible model
capabilities, exact tools, permissions, approvals, durable stores, and any required
sandbox.

The existing public APIs remain unchanged and continue to be supported directly.

## Consequences

- Simple chat can be configured lazily without task, team, sandbox, or database
  machinery.
- Advanced consumers retain full control of every existing registry and runtime.
- Cross-process continuation is advertised only when a host supplies a real durable
  relaunch adapter; reconnecting to status is not misrepresented as execution.
- The facade may create an in-process future that awaits the existing controller,
  but durable state remains authoritative and all task execution remains owned by
  `TaskScheduler`.
- No package root import, protocol, or browser package change is required.
