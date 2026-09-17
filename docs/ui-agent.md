# UI Agent runtime

Phase F adds the reusable browser half of the platform in
`packages/ui-agent`. It does not contain portfolio-specific routes, components,
or copy.

## Runtime boundary

The `AgentUIRuntime` owns connection state, event deduplication, Dynamic Island
state transitions, artifact accumulation, and semantic client-action execution.
Applications subscribe to immutable snapshots or use the React bindings.

The default `HttpSseTransport` uses:

- `GET /events?session_id=...` for named SSE events;
- `POST /input` for user input;
- `POST /capabilities` for action schemas and supported artifact types;
- `POST /actions/result` for structured client-action results.

The transport interface is public, so WebSocket, Realtime, native-mobile, or
test transports can replace HTTP/SSE without changing the runtime.

## Semantic action security

The browser never accepts selectors, scripts, or arbitrary function names. A
host registers a small allowlist such as `navigate`, `open_modal`, or
`prefill_form`, with a strict JSON Schema and handler. Unknown actions are
denied. Invalid arguments never reach application code. Each execution has an
abort signal, timeout, trace context, and structured success/failure response.

Server-side authorization remains mandatory. The client allowlist is a second
boundary, not a replacement for backend policy and approval checks.

## Dynamic Island states

The reducer models `idle`, `listening`, `composing`, `thinking`,
`tool_activity`, `waiting_approval`, `waiting_user`, `result`, and `compact`.
Protocol events drive transitions; visual treatment stays themeable by the
product. Artifacts are typed protocol objects rendered by host-owned registry
entries.

## Integration order

1. Construct a transport.
2. Register the product's allowed client actions.
3. Declare the artifact types the product can render.
4. Construct one runtime per mounted agent surface.
5. Mount the provider and Dynamic Island, or subscribe headlessly.
6. Connect with the authenticated session ID.

See `examples/ui-agent-react/App.tsx` for a portfolio-style integration shell.
