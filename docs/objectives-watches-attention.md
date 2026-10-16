# Objectives, watches, and attention

`ObjectiveManager` stores long-lived, user-scoped goals behind an explicit state
machine. Tenant, user, and assigned-agent identity comes from `ObjectiveContext`, not
model arguments. Terminal objectives cannot be resumed.
Completion is only available through an injected deterministic verifier; callers
cannot mark an objective completed with a raw state transition.

`WatchEngine` waits for structured conditions through event, webhook, or polling
strategies. Conditions use a bounded operator set and dotted payload fields; they are
never evaluated as source code. A match persists the watch result, resumes a waiting
objective when attached, and schedules a `watch_matched` lifecycle wakeup. Raw event
or probe payloads are not copied into wakeup metadata.

`AttentionEngine` maps severity deterministically:

- info: persist only;
- warning: persist for the next lifecycle cycle;
- action required: request an immediate wakeup;
- critical: request an immediate wakeup and call an optional host notifier.

The notifier is a product-owned port and does not grant the platform permission to
send messages. `SQLiteCoordinationStore` is the local durable reference for all three
subsystems. Distributed claims and cross-process transition locks remain R7 work.
