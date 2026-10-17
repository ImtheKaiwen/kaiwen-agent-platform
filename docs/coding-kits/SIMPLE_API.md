# Simple Coding API

`CodingKit` is an optional, additive facade over the existing agent runtime. It does
not add a second workflow engine, tool executor, team runtime, state store, or
permission system.

## Chat

```python
from kaiwen_agent.kits.coding import CodingKit

async with CodingKit.local(
    workspace="./project",
    provider="openai",
    model="your-model-id",
    user_language="tr",
) as kit:
    reply = await kit.agent().chat("Bu projenin mimarisini açıkla.")
    print(reply.text)
```

Construction is lazy. It does not call a model, inspect or write the workspace, or
start a subprocess. Chat exposes zero tools. A workspace path is an identity and
scope input; it grants no filesystem authority.

Provider credentials remain in the host environment used by the provider SDK. The
facade never accepts or serializes credentials. Install only the provider extra you
use (`kaiwen-agent[openai]`, `[gemini]`, or `[ollama]`). No model ID is assumed.

## Explicit action

Action mode requires a host-created `CodingExecutionBinding`. Its `ToolRegistry`,
`ToolExecutor`, permissions, exact `action_tools` allowlist, policy and approval gate
remain authoritative.

```python
report = kit.preflight(mode="action", tool_names=["workspace.read"])
if report.ok:
    result = await kit.agent().action("Read the manifest", tools=["workspace.read"])
```

Unknown tools, missing model capabilities, missing approvals and false sandbox
claims fail closed. Chat still receives no tools even when the binding has actions.

## Solo workflow

`agent.start(objective)` requires an explicit trusted binding containing the existing
`ObjectivePlanner`, `WorkflowController`, `DurableRunManager`, standards resolution,
real verifiers and any required sandbox. The facade creates the durable run and then
delegates execution to those components.

The binding must also supply a trusted `protected_input_fingerprint` callback for the
actual project/input snapshot. The facade deliberately does not substitute the text
objective hash for artifact provenance.

```python
report = kit.preflight(mode="workflow")
if not report.ok:
    raise RuntimeError(report.issues)

handle = await kit.agent().start("Implement and verify the approved change.")
result = await handle.wait(timeout=300)
```

`wait()` returns when the existing workflow returns a terminal or blocked outcome.
It does not turn missing evidence into success.

## Team workflow

Team mode is optional and never initialized by chat or solo execution. The host must
provide a `CodingTeamBinding` with a `ConfiguredCodingTeam`, the existing
`TeamRuntime`, and a launcher backed by existing `JobManager`/delegation semantics.

```python
report = kit.preflight(mode="team", team=True)
handle = await kit.team().start("Implement and independently review the change.")
```

The launcher is a host adapter, not another team engine. Role permissions, bounded
handoffs, job state and resource locks remain in the existing runtime.

## Hosted use

Never use `CodingKit.local` as authentication in a web or multi-user service. Use
`CodingKit.for_host` with an authenticated `RuntimeIdentity`, host-authorized
workspace, existing `AgentFactory`, durable stores and trusted execution binding.

```python
kit = CodingKit.for_host(
    identity=authenticated_identity,
    workspace=authorized_workspace,
    agent_factory=existing_agent_factory,
    provider_ref="host.openai",
    execution=approved_execution,
    model_capabilities=capability_registry,
    provider_preset=provider_preset,
)
```

## Locality and preflight

Pass `data_locality="local_only"` when data must remain local. A cloud-capable model
then produces `locality_violation`; the facade never silently falls back. Static
preflight is side-effect-free and cannot prove network reachability.

Stable error codes include `provider_not_registered`, `provider_capabilities_missing`,
`model_tool_unsupported`, `structured_plan_unsupported`, `tools_not_allowed`,
`approval_required`, `sandbox_missing`, `verifier_not_registered`,
`locality_violation`, `durable_store_missing`, and
`resume_configuration_mismatch`.

## Recovery and lifecycle

`kit.resume(run_id)` reads the existing durable run using the trusted owner identity
and rejects changed version pins. A `CodingRunHandle` is only a scoped reference to
durable state. `pause()` and `cancel()` require a scheduler-backed host control port;
without one they return explicit unsupported errors. `events()` requires an existing
owner-scoped event store.

Use `async with` or call `await kit.close()`. Only resources created by `local()` are
eligible for disposal. Injected hosted resources remain owned by the host.

## Current limitations

- The package does not provide a universally safe host-process sandbox.
- Provider capabilities must be registered truthfully before action/workflow mode.
- Team launching remains an explicit host adapter to `TeamRuntime` and `JobManager`.
- Detailed task/artifact projections after process restart require persisted workflow
  evidence; unknown fields are not fabricated.
- Static preflight is not a paid provider connectivity test.

The original `CodingKitFactory`, `CodingAgent`, `AgentRuntime`, and team APIs remain
supported for advanced composition.
