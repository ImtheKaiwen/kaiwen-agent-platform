# ADR 0008: Ship coding kits as opt-in platform modules

- Status: Accepted

## Context

Kaiwen Agent already provides the provider-neutral agent loop, runtime composition,
durable task execution, workflow controller, team delegation, policy, approval,
standards, verification, context, artifacts, and recovery boundaries. Developers
still need substantial host composition to use those primitives for a professional
coding workflow.

A coding experience needs reusable prompts, conditional standards, bounded workspace
tools, project discovery, and convenient single-agent and team composition. Putting
those concerns into core runtime modules would make plain chat depend on a coding
domain. Building a separate companion runtime would duplicate security and execution
authority.

## Decision

First-party coding support is an opt-in package subtree inside the existing
`kaiwen-agent` distribution:

- `kaiwen_agent.toolkits` contains generic, reusable, bounded tool adapters;
- `kaiwen_agent.kits.coding` contains coding-specific manifests, prompts, standards,
  discovery, verification, and composition helpers;
- neither subtree is imported by the package root or by core runtime modules;
- loading definitions performs no filesystem writes, process execution, network
  requests, provider construction, or registry mutation;
- hosts continue to own credentials, workspace roots, identities, stores, sandbox
  implementations, policy, approval, provider factories, and permission ceilings.

`CodingAgent` composes the existing `AgentFactory`, `AgentRuntime`,
`WorkflowController`, and Task Runtime. `CodingTeam` additionally composes the
existing `TeamRuntime`, `SubagentDelegator`, and `JobManager`. The kit does not create
a second model loop, scheduler, policy engine, approval system, standards engine, or
completion gate.

Optional external dependencies remain extras and are imported only when their
adapter is used. A separately published companion package may be reconsidered if the
coding surface later requires a materially different dependency or release cadence.

## Consequences

- Existing `Agent` and `AgentRuntime` consumers remain unaffected.
- Generic tool adapters can be reused without installing or selecting a coding kit.
- Coding definitions can be versioned and tested with the runtime while preserving a
  single distribution and compatibility matrix.
- Import-cycle tests and clean-install tests must prove that core does not depend on
  the optional coding modules.
- Selecting a kit or tool bundle never grants permissions or bypasses policy,
  approval, idempotency, audit, evidence, or recovery controls.
