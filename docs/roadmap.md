# Delivery roadmap

The detailed architecture lives outside product applications. This repository tracks
implementation status for the reusable packages.

## Completed

- [x] Phase A: repository boundaries, canonical JSON Schema, shared fixtures, CI.
- [x] Phase B: async Python core, fake provider, tool registry, in-memory stores.
- [x] Phase C: OpenAI Responses adapter, strict function schemas, structured output,
      permissions, approvals, idempotency, timeout/retry classification, usage events,
      and provider contract tests.
- [x] Phase D: session/run/event/audit ports, SQLite reference persistence, PostgreSQL
      adapter outline, SSE fan-out, trace propagation, and secret redaction.
- [x] Phase E: durable task state machine, DAG validation, scheduler, workers,
      dependencies, deterministic retry/cancellation, mailbox/checkpoints, resource
      locks, and global/per-agent concurrency limits.
- [x] Phase F: headless TypeScript UI runtime, semantic action registry, HTTP/SSE
      transport, capability discovery, React bindings, artifact renderers, and
      Dynamic Island state machine.
- [x] Phase R1: provider-neutral Realtime Core, explicit session lifecycle,
      tenant/user isolation, concurrent session limits, connection primitives, and
      deterministic fake provider.
- [x] Phase R2: OpenAI Live primary WebSocket adapter, server-authorized WebRTC
      bootstrap, text/audio commands, barge-in readiness, event normalization, and
      transport contract tests.
- [x] Phase R3: tenant-scoped conversation messages, text/voice transcript assembly,
      SQLite persistence, allowlisted task submission, and task status isolation.
- [x] Phase R2.1: trusted backend sideband attachment for existing browser WebRTC
      sessions, strict delegated tool schemas, identity binding, and safe tool
      execution without restarting the Live session or sending primary audio.

## Next

- [ ] Phase R4 / G: authenticated portfolio admin integration, WebRTC bootstrap route,
      Dynamic Island voice states, task notifications, and semantic UI dispatch.
- [ ] Phase R5: short-term context, memory recall, and memory write policy.
- [ ] Phase R6: production tenant isolation, quotas, policy configuration, and
      tenant-scoped observability.
- [ ] Phase R7: production scaling, distributed coordination, recovery, and load tests.
- [ ] Phase R8: optional telephony gateway and phone channel adapters. Phone media must
      enter the same Realtime Core; providers must not bypass policy or persistence.
- [ ] Phase R9: scheduled/objective calls, daily reports, explicit consent, and call
      summaries written through the memory policy.
- [ ] Phase R10: security hardening, abuse controls, retention enforcement, and
      production readiness review.

Publishing, deployment, and GitHub pushes remain separate explicit release steps.
