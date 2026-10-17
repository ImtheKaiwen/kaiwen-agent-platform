# Coding standards and verification

The Coding Kit installs independent versioned `StandardsPack` definitions. They use
the existing `StandardsResolver`, `VerifierRegistry`, and `CompletionGate`; they do
not authorize tools or create workflow steps.

Available pack IDs at version 1:

- `coding.foundation`
- `coding.documentation`
- `coding.tests`
- `coding.architecture`
- `coding.security`
- `coding.performance`
- `coding.ci`
- `coding.data`
- `coding.api`
- `coding.ui-accessibility`
- `coding.ui-minimal-neutral`

Applicability uses one explicit fact per conditional requirement. Unknown facts stay
unresolved. For example, `has_database=false` disables the data requirement and
`has_ui=false` disables both UI requirements. The neutral design consistency check
is advisory (`should`); executable accessibility evidence remains a conditional
mandatory requirement when that pack is selected for a UI project.

## Evidence contract

`install_coding_verifiers()` registers concrete JSON-artifact verifiers. A matching
artifact must be owned by the trusted tenant/user, belong to the current run, carry
the current protected-input fingerprint, declare the requirement ID and an allowed
evidence type, and contain a JSON object with an observed status. Test and acceptance
evidence also requires exit code zero for a pass.

Example artifact labels:

```json
{
  "requirement_id": "coding.tests.run",
  "evidence_type": "test_run",
  "input_fingerprint": "trusted-current-source-fingerprint"
}
```

Example content:

```json
{
  "status": "pass",
  "exit_code": 0,
  "command_id": "python.pytest"
}
```

Missing, stale, cross-owner, cross-run, malformed, or status-unknown evidence is
inconclusive. A failed mandatory check blocks completion. A failed advisory check
produces a warning. A CI configuration artifact proves only static configuration
validation and is not evidence that hosted CI passed.

Evidence producers remain host-owned. A command result is not automatically promoted
to completion evidence unless the host records the correctly scoped artifact after
the trusted check actually runs.
