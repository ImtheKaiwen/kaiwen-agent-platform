# Trigger routing

`TriggerRouter` prevents every incoming event from waking an agent. Product hosts
provide typed `TriggerRule` instances; the router filters payload fields, rejects
duplicate event IDs, debounces bursts, coalesces related events, and creates one
persisted lifecycle wakeup through `WakeupManager`.

Event payloads are untrusted. Matching is equality-only over configured dotted
paths; the runtime never evaluates expressions or copies raw payloads into wakeup
metadata. Tenant-constrained rules cannot match another tenant.
Debounce and dedupe windows use the host receipt clock, never the event-provided
timestamp, so replayed payloads cannot move scheduler deadlines.

Call `flush_due()` from the host scheduler. A failed wakeup write restores the
claimed batch for retry. `InMemoryTriggerStore` is the deterministic reference
implementation; multi-process durable claiming belongs to the production
coordination phase.
