# ADR 0007: Use safe boundaries and at-least-once runtime recovery

- Status: Accepted

## Context

Provider streams, model-local continuation state, task checkpoints, conversations,
artifacts, approvals, and external side effects have different durability semantics.
Treating one transcript or summary as complete execution state would make recovery
unsafe. External systems cannot generally promise exactly-once behavior.

## Decision

Durable workflow mode records a separate owner-scoped runtime run and immutable
version pins. Recovery resumes from the latest durable safe boundary, not the last
generated token. Conversation history, compacted context, execution state, and
artifacts/evidence remain separate stores.

Side-effecting work records a stable action intent and idempotency identity before
execution, then stores the result or receipt after execution. An interrupted action
whose external outcome cannot be reconciled becomes blocked or requires human
review; it is not retried blindly. Pending approvals remain pending after restart.
Startup recovery requires exclusive ownership through a lease or an equivalent host
guarantee.

Durable mode fails configuration when required durable stores are absent. It never
silently falls back to in-memory state. Execution remains at-least-once; stronger
guarantees require provider idempotency and reconciliation support.

## Consequences

- Provider state may be discarded and reconstructed from canonical messages when it
  cannot be serialized safely.
- Secrets and hidden reasoning are excluded from checkpoints.
- `TaskScheduler` remains the durable task-state authority and `JobManager` remains
  its user-facing projection.
- Pause, cancel, instructions, and approvals take effect at explicit cooperative
  boundaries.
