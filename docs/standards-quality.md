# Standards and runtime quality

Standards describe measurable delivery requirements. They do not grant permissions,
execute tools, replace policy, or become model-authored workflow state.

`StandardsPack` and `RequirementDefinition` are immutable and versioned. A
`WorkspaceProfile` may pin exact pack versions. `StandardsResolver` evaluates only
explicit boolean condition facts and rejects conflicting definitions instead of using
last-writer-wins. An unknown condition remains unresolved.

`VerifierRegistry` contains host-owned implementations. The core package does not
ship domain verifiers such as test runners, citation checkers, or CI clients. A
missing or failing verifier returns `inconclusive`, never pass.

`CompletionGate` validates every evidence reference through `ArtifactManager` using
trusted tenant/user identity. Passing evidence must belong to the current run, match
the protected-input fingerprint, and declare one of the requirement's allowed
evidence types. Mandatory fail or inconclusive results block completion; mandatory
approval requests remain pending; `should` failures are warnings.

`RepairTracker` only provides deterministic attempt, replan, and repeated-fingerprint
bounds. It does not schedule work or call a model. A later workflow controller may
use these decisions while `TaskScheduler` remains the execution authority.

Offline `EvaluationRunner` remains a separate benchmark/test facility and is not a
runtime completion gate.
