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

The core calls a small `ModelProvider` protocol. Provider response IDs remain local
to an individual run and are passed back explicitly, so a provider adapter can be
shared by concurrent sessions without sharing conversation state. OpenAI integration
is an optional adapter and does not leak SDK types into the core.

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
