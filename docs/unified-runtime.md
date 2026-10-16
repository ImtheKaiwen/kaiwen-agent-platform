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

Implemented: `AgentRuntime` preserves the legacy loop, hides every tool in chat,
requires an explicit trusted tool-name subset for action, carries trusted identity
into `AgentContext`, and rejects workflow mode until its durable controller exists.

### U2 — Definitions, profiles, and version pins

Add immutable `AgentDefinition`, its registry, a provider registry/factory boundary,
and a strict programmatic `WorkspaceProfile`. Resolve tool visibility against
`ToolRegistry` and declared capabilities, while policy remains authoritative.

Implemented: exact `id@version` agent, prompt, capability, and workspace references
are resolved before execution. `AgentFactory` rejects missing or out-of-scope tools,
providers, permissions, memory namespaces, and capability manifests; creates a fresh
provider-backed `AgentRuntime`; and attaches immutable configuration pins plus a
deterministic toolset checksum to runtime context. These pins are observational until
U5 persists them with durable run state.

### U3 — Context integration and compaction

Compose scoped context for the model request, introduce provider-aware token counting,
offload large outputs through artifacts, and add conservative structured compaction.
Canonical instructions, policy, task state, and acceptance criteria are never sourced
from a lossy summary.

Implemented: runtime context composition is optional and bounded by provider-aware
token counting, output/request reservations, and selected tool-schema cost. Rolling
compaction has structured provenance and preservation checks, keeps raw history, and
rejects unsafe summaries. Large model-facing tool results can be offloaded to
owner-scoped artifacts. The legacy `Agent` and `ModelProvider.respond()` signatures
remain unchanged.

### U4 — Standards and runtime quality

Add versioned standards, deterministic requirement resolution, verifier registration,
owner-scoped evidence, completion gates, and bounded stagnation-aware repair models.
No domain-specific verifier implementation belongs in core.

Implemented: immutable standards packs and deterministic condition/conflict
resolution remain separate from prompts, policy, and skills. Host verifiers return
structured results; completion gates validate owner/run/fingerprint/type-scoped
artifact evidence and fail inconclusive when a mandatory verifier or evidence is
missing. Repair/replan/stagnation tracking is bounded and does not execute work.

### U5 — Durable run state and recovery

Add an owner-scoped `RuntimeRunStore`, SQLite reference persistence, version pins,
action intents, durable approvals/idempotency receipts, startup reconciliation, and
safe pause/resume/cancel. Durable configuration fails closed without durable stores.

Implemented: workflow state is stored separately from the legacy `AgentRun` and pins
trusted owner identity plus the exact runtime configuration. `DurableRunManager`
provides owner-scoped safe lifecycle transitions without becoming an executor.
Side-effecting `ToolExecutor` composition can persist a stable action intent before
execution, bind a one-time durable approval to the exact owner/conversation/tool/call,
and reuse a committed receipt after restart. SQLite reference stores cover run state,
action intents, approvals, and idempotency receipts. Startup reconciliation requires
an exclusive lease and converts interrupted executing actions to `uncertain`, blocking
their run instead of retrying an external effect blindly. Workflow execution itself
remains disabled until U6 compiles plans into the existing Task Runtime.

### U6 — Autonomous single-agent workflow

Add structured plan validation and compilation into the existing `TaskGraph`, then a
bounded controller that advances through execute, verify, repair, replan, blocked, or
terminal decisions. Side-effecting autonomy is available only after U5.

Implemented: untrusted structured plans are constrained by owner identity, worker,
capability, resource, graph, size, and strict-JSON validation before compilation into
the existing `TaskGraph`. `WorkflowController` delegates all execution to
`TaskScheduler`, holds the resolved standards fixed, requires `CompletionGate`
evidence before completion, and bounds repair/replan cycles with stagnation detection.
Unexpected scheduler or completion-gate failures terminally fail the durable run.
`AgentRuntime.run()` remains fail-closed for `workflow`; hosts compose the structured
workflow controller explicitly until a stable model-planning input contract exists.

### U7 — Optional teams

Compose lead and child runtime instances through the existing jobs and delegation
boundary. Enforce capability intersection, private context views, bounded depth and
fanout, resource locks, structured handoff, and shared completion contracts. The
single-agent API remains independent.

Implemented: immutable `TeamDefinition` records bind exact registered lead/member
agent versions and role capability ceilings. `TeamRuntime` performs deterministic
least-privilege profile selection, forwards only typed context references through the
existing `SubagentDelegator`, and executes children through the existing `JobManager`
and Task Runtime. Central delegation policy remains authoritative for depth,
concurrency, per-run limits, and capability intersection. Child results cross the
boundary only as a bounded `TeamHandoff`; raw context, logs, and undeclared result
fields are not exposed. Dynamic agent synthesis is intentionally unsupported.

### U8 — Provider capabilities and adapters

Add technical `ModelCapabilities` separately from agent `CapabilityManifest`, then
optional Gemini and Ollama adapters, tool strategies, data-locality-aware fallback,
and provider contract tests. Provider SDKs never execute tools directly.

Implemented: immutable technical `ModelCapabilities` and a provider/model registry
remain separate from authorization-oriented agent manifests. Routing enforces local
and regional data constraints before policy evaluation, so local-only inputs cannot
fall through to cloud routes. Optional Gemini Generate Content and Ollama Chat
adapters normalize native function-call proposals while keeping execution in the
central runtime; text-only strategy neither exposes tool schemas nor accepts tool
calls. Unsupported structured/delegated strategies fail during composition rather
than silently weakening safety.

### U9 — Speech and optional ecosystem ports

Add lightweight STT/TTS/transcript contracts and fake adapters that compose with the
existing Realtime Core. Filesystem, shell, browser, MCP, document, CI, and domain
integrations remain optional host adapters.

Speech slice implemented: provider-neutral recognition, synthesis, transcript,
metadata-only audio artifact reference, and ephemeral pipeline contracts are
available with deterministic fakes. The pipeline requires trusted explicit audio
processing permission, carries one tenant/user/session/conversation identity through
STT, text handling, and TTS, and never persists raw audio. Native realtime speech
continues to use the separate Realtime Core. Heavy engines and ecosystem adapters
remain optional follow-up work.

Ecosystem foundation implemented: the optional workspace filesystem adapter accepts
only host-configured roots and a trusted workspace binding, canonicalizes every path,
blocks traversal and symlink escape, separates read/write permissions, bounds bytes,
and requires approval for writes. MCP tools become executable only through a trusted
host binding whose schema exactly matches the discovered descriptor; permissions,
side-effect classification, approval, idempotency, audit, and execution remain in the
central `ToolExecutor`. Discovery alone grants no authority. General shell execution,
delete operations, browser engines, documents, CI, and domain tools are not included.

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
