# kaiwen-agent

Provider-neutral, asynchronous Python runtime for building tool-using agents.
Product applications own their prompts, domain tools, authorization context,
persistence choice, and HTTP surface.

```bash
pip install "kaiwen-agent[openai]"
```

For OpenAI Live primary WebSocket support:

```bash
pip install "kaiwen-agent[openai-live]"
```

## Minimal agent

```python
import asyncio

from pydantic import BaseModel

from kaiwen_agent import Agent, AgentContext, tool
from kaiwen_agent.models.openai import OpenAIResponsesProvider
from kaiwen_agent.types import AgentInput


class ProjectQuery(BaseModel):
    category: str | None = None


@tool(
    name="projects.read",
    description="List projects visible to the current user",
    input_model=ProjectQuery,
    permissions={"projects.read"},
)
async def read_projects(
    context: AgentContext,
    query: ProjectQuery,
) -> list[dict[str, str]]:
    repository = context.services["projects"]
    return await repository.list(category=query.category)


async def main() -> None:
    agent = Agent(
        name="portfolio",
        model=OpenAIResponsesProvider(
            model="your-model-id",
            instructions="Help visitors discover relevant products.",
            store=False,
        ),
        tools=[read_projects],
        permissions={"projects.read"},
    )
    result = await agent.run(
        AgentInput(text="Show me the games"),
        context=AgentContext(
            session_id="session-id",
            permissions=frozenset({"projects.read"}),
            services={"projects": your_repository},
        ),
    )
    print(result.text)


asyncio.run(main())
```

For a single-agent composition that keeps normal chat tool-free and makes action
tools explicit:

```python
from kaiwen_agent import AgentRuntime, RuntimeIdentity

runtime = AgentRuntime(name="assistant", model=provider, tools=[read_projects])
reply = await runtime.chat(
    "Merhaba",
    identity=RuntimeIdentity(session_id="session-id"),
)
```

`AgentRuntime.action()` exposes only the tool names selected by trusted host code.
Workflow mode remains unavailable until durable run/recovery and completion-gate
composition is installed; it never falls back to an unsafe in-memory workflow.

`OPENAI_API_KEY` is read by the OpenAI SDK from the server environment. The
runtime never stores it and it must never be exposed to browser code.

## Runtime capabilities

- Provider-neutral async agent loop and deterministic fake provider.
- Typed Pydantic tool inputs and deny-by-default permission intersection.
- Approval, idempotency, timeout, and retry handling for side effects.
- Session, run, event, and audit ports with a SQLite reference adapter.
- SSE event fan-out and trace propagation.
- Durable task graphs, workers, checkpoints, mailbox control, resource locks,
  cancellation, and bounded concurrency.
- Optional OpenAI Responses API adapter.
- Provider-neutral Realtime sessions, OpenAI Live/WebRTC adapters, durable
  text-and-voice conversations, and allowlisted background task delegation.
- Trusted OpenAI Live sideband execution through the same permission, approval,
  idempotency, and audit pipeline used by text agents.
- Deterministic lifecycle and central policy runtimes, bounded context assembly,
  short-term session summaries, and policy-gated long-term memory.
- Non-blocking background jobs projected onto the existing Task Runtime, including
  progress events, cooperative cancellation, parent-child progress, and recovery.
- A deterministic Trigger Router that filters, deduplicates, debounces, and
  coalesces untrusted events before scheduling lifecycle wakeups.
- Policy-gated model routing, hierarchical runtime budgets, immutable versioned
  prompt and declarative skill registries, owner-scoped artifacts, and inspectable
  capability manifests.
- Structured evaluation, observation-only replay, fail-closed simulation,
  tenant-scoped redacted dead letters, backpressure, optional Redis coordination
  leases with fencing tokens, fixed-catalog tenant-scoped metrics, heartbeat health,
  and an allowlisted server-side secret-provider boundary.
- Optional PostgreSQL full-text + pgvector hybrid memory retrieval via
  `kaiwen-agent[postgres-memory]`.
- Optional Redis distributed lease coordination via `kaiwen-agent[redis]`.

Realtime usage and integration boundaries are documented in the repository's
`docs/realtime.md`, `docs/openai-live.md`, and `docs/conversation-bridge.md` files.

## Side effects

Tools marked `reversible` or `destructive` receive a runtime idempotency key.
Set `requires_approval=True` and supply an application-owned `ApprovalGate` for
publishing, deleting, deploying, calling, or sending messages. Applications
must still perform authorization inside their own service boundary. Memory setup and
its trust boundaries are documented in `docs/long-term-memory.md`.

## Coding-agent handoff

When asking another coding agent to integrate this package, provide the root
repository files `AGENTS.md` and `docs/consumer-agent-brief.md`. The complete,
provider-free example is in `examples/basic-agent`.
