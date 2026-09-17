# Brief for an agent integrating Kaiwen Agent Platform

Give this document and the relevant package README to a coding agent before it
modifies a consuming project.

## Architecture in one minute

`kaiwen-agent` runs on the trusted server and owns model calls, tool policy,
approvals, state, and events. `@kaiwen/agent-ui` runs in the browser and owns UI
state plus a narrow allowlist of semantic host actions. Both sides communicate
with versioned contracts from `@kaiwen/agent-protocol`.

The product supplies its own domain tools, authorization context, prompts,
persistence adapter, routes, visual theme, and artifact components. The reusable
packages must not learn product-specific rules.

## Work order

1. Identify the server and browser boundaries in the target project.
2. Install pinned package versions; do not paste package source into the project.
3. Add server-side session authentication before exposing input or SSE routes.
4. Define the smallest possible domain-tool allowlist.
5. Define the smallest possible semantic client-action allowlist.
6. Map protocol artifacts to product-owned components.
7. Add contract, authorization, failure-state, and responsive tests.
8. Document every new product capability next to its registration point.

Start with `examples/basic-agent`, `examples/task-graph`, and
`examples/ui-agent-react`. Detailed subsystem contracts are under `docs/`.
