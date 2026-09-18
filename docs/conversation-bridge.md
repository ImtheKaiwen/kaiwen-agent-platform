# Conversation and task bridge

R3 connects ephemeral realtime provider sessions to durable application-owned
conversations and the existing task runtime.

## Conversation ownership

`RealtimeSession` remains temporary. `conversation_id` is stable across reconnects,
text input, voice input, and future clients. Every stored message is scoped by
`tenant_id` and `conversation_id`; provider session IDs are metadata, not authority.

```python
from kaiwen_agent.realtime import InMemoryConversationStore, RealtimeBridge

conversations = InMemoryConversationStore()
bridge = RealtimeBridge(session_manager, conversations=conversations)

# Consume voice/provider events for one active session.
await bridge.run(realtime_session.id)

# Text joins the same durable conversation.
await bridge.send_text(realtime_session.id, "Create today's plan")
```

Transcript deltas are buffered in memory. A user buffer is finalized when assistant
output begins; assistant output is finalized on `realtime.turn.completed`. Disconnect
or failure flushes remaining text with `metadata.partial = true`. Raw audio is never
written to the conversation store.

`SQLitePersistence` implements `ConversationStore` for local deployments. Production
adapters must preserve the same tenant-scoped query boundary.

## Background task delegation

Long work is submitted through `TaskSubmissionPort`; the realtime conversation does
not instantiate or block on a `TaskScheduler`.

```python
from kaiwen_agent.realtime import RealtimeTaskBridge

tasks = RealtimeTaskBridge(
    session_manager,
    product_task_queue,
    allowed_agents={"planner", "analyst"},
    default_agent="planner",
)

reference = await tasks.delegate(
    realtime_session.id,
    "Analyze the repository and prepare a timeline",
)
```

Agent selection is deny-by-default. Tenant, user, and conversation identity come from
the trusted realtime session record rather than model-generated tool arguments. Task
status lookups return not-found across tenant or user boundaries to avoid disclosing
the existence of another tenant's task.

The consuming application owns the submission adapter that queues the `AgentTask` for
its scheduler/workers. Task completion notifications and UI dispatch policy belong to
the authenticated admin integration phase.
