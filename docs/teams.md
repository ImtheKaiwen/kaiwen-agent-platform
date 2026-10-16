# Optional agent teams

Teams are an optional composition layer. They do not replace `AgentRuntime`, execute
models, schedule tasks, or grant authority.

`TeamDefinition` pins one lead and a finite set of member roles to exact registered
`AgentDefinition` versions. Each role declares a capability ceiling that must be a
subset of the registered agent permissions. `TeamDefinitionRegistry` is immutable at
an existing `id@version`.

`TeamRuntime.delegate()` chooses an explicitly requested role or deterministically
selects the least-privileged registered member that satisfies the request. It then
passes a normal `DelegationRequest` to `SubagentDelegator`. The existing central
`DelegationPolicy` remains responsible for delegate allowlists, depth, concurrency,
per-run limits, and capability intersection. `JobManager` and `TaskScheduler` remain
the only job and task execution authorities.

Context handoff accepts named references, not raw child histories. Reserved pinning
references bind each job to its team, member version, and role. Completed work is
returned as `TeamHandoff`, which includes only a bounded summary, artifact/evidence
references, blockers, and follow-up suggestions. Arbitrary worker result fields,
private scratchpads, and logs do not cross the child boundary.

Nested delegation is available only to members explicitly marked `may_delegate` and
must name the owned parent job. Resource conflicts continue to use Task Runtime
resource keys. Dynamic template instantiation and unrestricted agent synthesis are
not supported.
