# Integration contract for coding agents

Use this file when assigning integration work to an AI coding agent.

## Objective

Connect a product UI to an existing Kaiwen Agent backend without placing model
credentials or unrestricted browser control in the client.

## Required sequence

1. Install `@kaiwen/agent-ui`, `@kaiwen/agent-protocol`, and the host project's
   compatible React version.
2. Create an `ActionRegistry` containing only product-approved semantic actions.
3. Give every action a strict JSON Schema with `additionalProperties: false`.
4. Implement actions through application APIs such as the router or modal store;
   never accept CSS selectors, JavaScript strings, or arbitrary URLs from the model.
5. Construct `HttpSseTransport` with a same-origin backend base URL.
6. Construct `AgentUIRuntime`, passing the action registry and supported artifact
   types.
7. Mount `AgentUIProvider` once around the interactive surface.
8. Render `DynamicIsland` or build a product-specific UI with `useAgentUI`.
9. Register explicit artifact renderers. Unknown artifacts must render nothing or
   a safe fallback.
10. Test disconnected, thinking, tool, approval, error, result, and mobile states.

## Backend contract

The reference transport expects:

- `GET {baseUrl}/events?session_id=...` as named SSE events;
- `POST {baseUrl}/input`;
- `POST {baseUrl}/capabilities`;
- `POST {baseUrl}/actions/result`.

All events use `@kaiwen/agent-protocol`. Authentication, session ownership,
permissions, approval policy, rate limits, and model keys stay on the server.

## Completion criteria

- No API key is present in browser code or `NEXT_PUBLIC_*` variables.
- Unknown actions and invalid arguments cannot invoke application handlers.
- The runtime disconnects when its provider unmounts.
- Keyboard and screen-reader labels are present.
- The layout works at 320 px width.
- Unit tests cover every registered semantic action.

See `README.md` for API examples and the repository's
`examples/ui-agent-react/App.tsx` for a complete integration shell.
