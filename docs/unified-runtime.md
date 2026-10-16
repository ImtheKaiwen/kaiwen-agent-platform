# Unified runtime extension

This document adapts the unified runtime proposal to the current repository. The
existing runtime components remain authoritative; the extension composes them and
does not replace them.

## Current baseline

The package already provides the model/tool `Agent` loop, policy and tool safety,
Task Runtime, jobs and bounded delegation, lifecycle wakeups, context and memory,
model routing and budgets, registries, artifacts, evaluation and replay, realtime,
and production-control ports. Distributed leases, atomic SQLite budget reservations,
job-result lifecycle wakeups, dead letters, and tenant-scoped metrics are also part
of the baseline.

The extension must not recreate any of those systems. In particular:

- `TaskScheduler` is the only durable task executor;
- `JobManager` projects background work over that executor;
- `LifecycleRuntime` schedules wake/observe cycles and is not an agent task runner;
- `AgentRuntime` will be a single-agent-first facade over these components;
- `TeamRuntime` will be optional composition over isolated `AgentRuntime` instances.

## Confirmed gaps

- There is no composition facade, agent-definition registry, workspace profile, or
  provider factory.
- `Agent.run()` does not yet consume `ContextBuilder`, `ModelRouter`, `BudgetEngine`,
  or prompt/version pins.
- Session summaries are stored but not generated through a compaction pipeline.
- `AgentRun` is intentionally small and is not sufficient for resumable workflows.
- Approval is currently an injected one-shot gate and idempotency defaults to memory;
  durable pending approval, action intent, receipts, and reconciliation are absent.
- Run-control mailbox state is process-local, provider continuation state is not
  generally serializable, and artifacts have no bundled durable production adapter.
- Offline evaluation exists; runtime standards, evidence verifiers, completion gates,
  bounded repair, and stagnation detection do not.
- Gemini, Ollama, model capability discovery, and provider-neutral speech pipeline
  contracts do not exist.

These gaps do not block the chat fast path. They do block claims of crash-safe,
side-effecting autonomous workflow execution.

## Delivery order

### U0 — Baseline and contracts

Accepted ADRs define single-agent-first composition, standards separation, and
at-least-once recovery. Compatibility tests pin the legacy public entry points.

### U1 — Minimal AgentRuntime

Add trusted runtime identity, explicit mode and autonomy models, composition
validation, and `chat`/bounded synchronous `action` paths over the existing `Agent`.
No scheduler, team, or quality gate is created for chat.

### U2 — Definitions, profiles, and version pins

Add immutable `AgentDefinition`, its registry, a provider registry/factory boundary,
and a strict programmatic `WorkspaceProfile`. Resolve tool visibility against
`ToolRegistry` and declared capabilities, while policy remains authoritative.

### U3 — Context integration and compaction

Compose scoped context for the model request, introduce provider-aware token counting,
offload large outputs through artifacts, and add conservative structured compaction.
Canonical instructions, policy, task state, and acceptance criteria are never sourced
from a lossy summary.

### U4 — Standards and runtime quality

Add versioned standards, deterministic requirement resolution, verifier registration,
owner-scoped evidence, completion gates, and bounded stagnation-aware repair models.
No domain-specific verifier implementation belongs in core.

### U5 — Durable run state and recovery

Add an owner-scoped `RuntimeRunStore`, SQLite reference persistence, version pins,
action intents, durable approvals/idempotency receipts, startup reconciliation, and
safe pause/resume/cancel. Durable configuration fails closed without durable stores.

### U6 — Autonomous single-agent workflow

Add structured plan validation and compilation into the existing `TaskGraph`, then a
bounded controller that advances through execute, verify, repair, replan, blocked, or
terminal decisions. Side-effecting autonomy is available only after U5.

### U7 — Optional teams

Compose lead and child runtime instances through the existing jobs and delegation
boundary. Enforce capability intersection, private context views, bounded depth and
fanout, resource locks, structured handoff, and shared completion contracts. The
single-agent API remains independent.

### U8 — Provider capabilities and adapters

Add technical `ModelCapabilities` separately from agent `CapabilityManifest`, then
optional Gemini and Ollama adapters, tool strategies, data-locality-aware fallback,
and provider contract tests. Provider SDKs never execute tools directly.

### U9 — Speech and optional ecosystem ports

Add lightweight STT/TTS/transcript contracts and fake adapters that compose with the
existing Realtime Core. Filesystem, shell, browser, MCP, document, CI, and domain
integrations remain optional host adapters.

### U10 — Hardening and DX

Complete crash, multitenant, prompt-injection, failover, pressure, budget, and cold
install matrices. Add provider-free examples and documentation. Protocol schemas are
expanded only when a stable browser-visible semantic event is actually required.

## Non-goals

- No product routes, prompts, branding, authentication, or domain tools.
- No second scheduler, job manager, policy engine, memory store, or model loop.
- No unrestricted agent synthesis, recursive delegation, or infinite repair loops.
- No silent cloud fallback for local-only or restricted data.
- No completion decision based only on an agent's claim.
