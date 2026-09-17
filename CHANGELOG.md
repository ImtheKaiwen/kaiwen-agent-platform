# Changelog

## 0.1.0a2 — 2026-09-17

- Fix multi-step OpenAI tool execution when `store=False`.
- Carry provider-owned continuation state inside a single agent run without sharing
  conversation state between sessions.
- Preserve encrypted reasoning items for stateless Responses API continuation.
- Expand the OpenAI smoke example to verify a real two-turn tool call.

## 0.1.0a1 — 2026-09-17

- Initial alpha release of the Python runtime and OpenAI adapter.
- Initial npm releases of the shared protocol and headless UI runtime.
