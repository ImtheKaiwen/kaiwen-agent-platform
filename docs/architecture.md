# Architecture boundary

```text
Product application
  -> product-owned agent configuration and domain tools
  -> kaiwen-agent provider-neutral runtime
  -> provider adapter

Browser application
  -> product-owned visual theme and semantic handlers
  -> @imthekaiwen/agent-ui headless runtime
  -> versioned @imthekaiwen/agent-protocol events
```

The backend is the decision authority. Browser actions are semantic, allowlisted,
validated, and report a structured result. Arbitrary JavaScript or DOM selectors are
not part of the protocol.

## Text provider boundary

The core calls a small `ModelProvider` protocol. Opaque provider state remains local
to an individual run and is passed back explicitly, so a provider adapter can be
shared by concurrent sessions without sharing conversation state. The OpenAI adapter
uses response IDs when storage is enabled and carries response output items when
running statelessly. OpenAI integration is optional and does not leak SDK types into
the core.

## Realtime provider boundary

`kaiwen_agent.realtime` owns logical live-session state, tenant/user isolation,
concurrency limits, and provider-neutral connection primitives. Provider adapters own
transport details such as WebRTC, WebSocket, ephemeral credentials, audio formats,
and provider event translation. Provider SDK objects never cross into the core.

High-frequency audio and transcript deltas use a connection-local ephemeral event
stream. Durable session lifecycle events use a separate runtime event contract. The
shared browser protocol is not expanded until the conversation bridge can expose a
small, stable set of semantic events.

Public text/SSE assistants and authenticated admin live sessions are separate product
surfaces. Realtime credentials are issued server-side and scoped to one user,
tenant, client, and logical conversation.

## Conversation bridge

Realtime sessions are temporary transports; conversations are durable application
history. The conversation bridge assembles provider transcript fragments into
tenant-scoped text messages and never persists raw audio. Text and voice inputs share
the same conversation ID even when provider sessions reconnect.

Long work crosses a narrow task-submission port. The realtime layer does not create a
scheduler or execute workers. Agent selection is allowlisted, while tenant/user
identity comes from trusted session state rather than model-generated arguments.

## Tool safety order

```text
Input validation
  -> permission intersection
  -> approval gate
  -> idempotency lookup
  -> timeout/retry execution
  -> idempotency write
  -> lifecycle event
```

Unknown tools are rejected by the registry. Approval defaults to unavailable rather
than implicitly allowing an action.
