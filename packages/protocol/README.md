# @imthekaiwen/agent-protocol

Canonical TypeScript types and JSON Schemas shared by Kaiwen agent backends,
browser runtimes, tests, and product applications.

```bash
npm install @imthekaiwen/agent-protocol
```

```ts
import type { AgentArtifact, AgentEvent, ClientAction } from "@imthekaiwen/agent-protocol";
```

The package exports runtime `AGENT_EVENT_TYPES` and `SCHEMA_VERSION` constants.
JSON Schemas are available through subpaths such as:

```ts
import eventSchema from "@imthekaiwen/agent-protocol/schemas/event-envelope.schema.json";
```

Agent events may include nullable `tenant_id` and `user_id` owner fields. They are
optional for compatibility with older producers; absence never means public or
globally readable. Backend storage APIs remain responsible for exact owner-scope
checks.

Do not copy these contracts into product repositories. Depend on an explicit
package version so protocol changes remain observable and testable.
