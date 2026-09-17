# @imthekaiwen/agent-ui

Headless, framework-neutral browser runtime plus optional React bindings for the
Kaiwen Agent Platform. Product applications keep ownership of routing, modals,
forms, permissions, and visual identity.

## What it provides

- Versioned agent-event consumption over a replaceable transport.
- Deny-by-default semantic client action registry with JSON Schema validation,
  timeouts, and structured results.
- Action and artifact capability discovery during connection.
- Deterministic Dynamic Island state reducer.
- Framework-neutral artifact registry.
- React provider, hooks, React artifact registry, and a themeable Dynamic Island.
- HTTP command + named SSE event reference transport.

## Headless setup

```ts
import {
  ActionRegistry,
  AgentUIRuntime,
  HttpSseTransport,
} from "@imthekaiwen/agent-ui";

const actions = new ActionRegistry().register({
  name: "navigate",
  description: "Navigate within the host application",
  schema: {
    type: "object",
    additionalProperties: false,
    required: ["path"],
    properties: { path: { type: "string" } },
  },
  handler: ({ path }: { path: string }) => window.history.pushState({}, "", path),
});

const runtime = new AgentUIRuntime(
  new HttpSseTransport({ baseUrl: "/agent" }),
  actions,
  ["project_card", "task_progress"],
);

await runtime.connect("session-id");
await runtime.submit("Show me the products");
```

## React setup

```tsx
import { AgentUIProvider, DynamicIsland } from "@imthekaiwen/agent-ui/react";

<AgentUIProvider runtime={runtime} sessionId="session-id">
  <DynamicIsland
    labels={{ idle: "Kai'ye sor", thinking: "Düşünüyor" }}
    renderArtifact={(artifact) => <ProductArtifact artifact={artifact} />}
  />
</AgentUIProvider>;
```

Client actions are capabilities, not arbitrary DOM instructions. The server can
only request actions that the host explicitly registers, and every payload is
validated before its handler runs.
