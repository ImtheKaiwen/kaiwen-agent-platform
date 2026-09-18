# ADR 0004: Separate planning from durable task execution

- Status: Accepted

## Context

Agent plans may contain long-running, concurrent, retryable, or interruptible work.
Letting a model directly mutate scheduler state or inject instructions into arbitrary
running code would make recovery and concurrency behavior nondeterministic.

## Decision

Planning produces tasks and dependencies, but only `TaskScheduler` changes execution
state. Workers are registered under stable allowlisted IDs and cooperate at explicit
checkpoints. Pause, cancellation, and new instructions are applied at those safe
boundaries. Resources are acquired atomically, retries require declared stable error
codes, and generic failures are terminal by default.

Realtime delegates long work through the narrow task-submission port; it does not own
or block on the scheduler.

## Consequences

- Task execution is resumable, auditable, bounded, and deterministic under failure.
- Worker implementations must expose meaningful checkpoints for responsive control.
- New execution backends must preserve scheduler ownership, isolation, retry, and
  resource-lock semantics.
