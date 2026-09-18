# Realtime Core

`kaiwen_agent.realtime` is the provider-neutral lifecycle layer for live voice and
multimodal sessions. It is safe to reuse from admin web, mobile, and telephony
adapters without coupling the runtime to one product or provider SDK.

## What R1 includes

- Explicit session states and guarded transitions.
- Tenant- and user-scoped identity on every durable lifecycle event.
- Global, per-tenant, and per-user concurrent session limits.
- Text, audio, interruption, reconnect, and disconnect connection primitives.
- Provider and storage protocols with in-memory reference implementations.
- A deterministic fake provider for application integration tests.

Provider audio chunks and other high-frequency events stay on the local
`RealtimeProviderEvent` stream. Durable lifecycle events use
`RealtimeRuntimeEvent`. They are intentionally not part of the shared browser event
protocol yet; the conversation bridge will map only stable semantic events.

## Minimal integration

```python
from kaiwen_agent.realtime import (
    FakeRealtimeProvider,
    RealtimeSessionConfig,
    RealtimeSessionManager,
)

manager = RealtimeSessionManager([FakeRealtimeProvider()])
session = await manager.create_session(
    RealtimeSessionConfig(provider="fake", model="live-test"),
    conversation_id="conversation_123",
    tenant_id="tenant_123",
    user_id="user_123",
)

await manager.send_text(session.id, "Create today's project summary")
await manager.interrupt(session.id)
await manager.resume(session.id)
await manager.disconnect(session.id)
```

Application code should replace the fake provider and in-memory stores at its
composition root. Provider credentials and provider SDK objects remain server-side.

## Lifecycle

```text
created -> connecting -> active -> interrupted -> active
                         |              |
                         +-> reconnecting -> active
                         |
                         +-> closing -> closed

Any non-terminal provider setup/reconnect state may fail -> failed.
```

Closed and failed sessions are terminal. Reconnect creates a new provider connection
for the same logical runtime session and does not affect other sessions.

## Integration rules

- Always provide an application-owned `tenant_id`, `user_id`, and
  `conversation_id`; do not derive authorization from provider session IDs.
- Register providers explicitly. Unknown providers are denied.
- Treat in-memory stores as development/test adapters only.
- Do not expose provider secrets, raw SDK types, or sideband credentials to clients.
- Keep public text/SSE assistants separate from authenticated admin voice sessions.

The OpenAI Live implementation and WebRTC bootstrap are documented in
[`openai-live.md`](openai-live.md). R3 adds the durable conversation bridge,
transcript policy, semantic task delegation, and audit mapping.
