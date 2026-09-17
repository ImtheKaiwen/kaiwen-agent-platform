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

## Next

- [ ] Phase G: first portfolio integration after core contracts stabilize.

Publishing, deployment, and GitHub pushes remain separate explicit release steps.
