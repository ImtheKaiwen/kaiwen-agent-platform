# ADR 0003: Separate live transports from durable conversations

- Status: Accepted

## Context

Realtime provider connections are temporary and may reconnect, while users expect one
conversation to continue across text, voice, clients, and provider sessions. Audio and
transcript deltas are high-volume transport data and are unsuitable as the durable
application record.

## Decision

Realtime sessions remain provider-neutral, temporary transports. An
application-owned conversation ID is the durable identity and is always scoped by
trusted tenant and user context. The conversation bridge assembles stable text
messages from transcript fragments; raw audio is not persisted. Provider session IDs
are metadata, never authorization or conversation identity.

Privileged backend participation in a browser WebRTC session uses an official
sideband mechanism when available. It must not be simulated with undocumented
endpoints or parameters, and an attached sideband must not restart the session or act
as the primary audio transport.

## Consequences

- Reconnects can replace transport sessions without fragmenting user history.
- Persistence and memory operate on normalized conversation records rather than raw
  provider streams.
- Voice, browser, mobile, and future telephony adapters enter the same Realtime Core
  instead of creating parallel agent stacks.
