# Changelog

## 0.3.0a1 — 2026-09-18

- Add trusted OpenAI Live sideband attachment for existing browser WebRTC sessions.
- Register strict Responses-delegation tool schemas when creating Live sessions.
- Execute completed delegated function calls through the existing permission,
  approval, idempotency, retry, and audit pipeline.
- Bind sideband tool execution to the logical realtime session, tenant, and user.
- Keep sideband shutdown independent from primary WebRTC/SIP media and reject
  duplicate completed response events.

## 0.2.0a1 — 2026-09-18

- Add the provider-neutral Realtime Core with isolated session lifecycle,
  interruption/reconnect handling, and layered concurrency limits.
- Add the OpenAI Live primary WebSocket adapter and server-authorized WebRTC session
  bootstrap without exposing API credentials to clients.
- Add normalized audio, transcript, usage, error, and nested Responses events.
- Add tenant-scoped durable conversations that unify text and voice transcripts while
  keeping raw audio ephemeral.
- Add allowlisted background task submission and tenant/user-scoped task status.
- Extend `AgentContext` and `AgentTask` with optional tenant, user, client, and
  conversation identity fields.
- Add SQLite conversation persistence, fake transports, integration tests, and
  reusable Realtime/Live documentation.

## 0.1.0a2 — 2026-09-17

- Fix multi-step OpenAI tool execution when `store=False`.
- Carry provider-owned continuation state inside a single agent run without sharing
  conversation state between sessions.
- Preserve encrypted reasoning items for stateless Responses API continuation.
- Expand the OpenAI smoke example to verify a real two-turn tool call.

## 0.1.0a1 — 2026-09-17

- Initial alpha release of the Python runtime and OpenAI adapter.
- Initial npm releases of the shared protocol and headless UI runtime.
