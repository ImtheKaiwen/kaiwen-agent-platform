# ADR 0006: Separate standards from policy, prompts, skills, and verification

- Status: Accepted

## Context

Instructions, authorization, workflow templates, delivery requirements, and evidence
answer different questions. Combining them would let model-authored text weaken
security or allow a claimed result to substitute for an observed test, receipt, or
human approval.

## Decision

Keep the concepts separate:

- prompts provide versioned model instructions and style;
- policy authorizes, denies, modifies, reviews, or requires approval for actions;
- skills compile declarative workflow templates into the existing Task Runtime;
- standards define versioned delivery requirements and evidence expectations;
- verifiers evaluate evidence and return `pass`, `fail`, `inconclusive`, or
  `approval_required`;
- completion gates derive a terminal decision from resolved mandatory requirements.

Standards do not execute tools or grant permissions. Missing required verifiers and
unverifiable evidence are inconclusive, never successful. Deterministic evidence is
preferred to model judgment, and human approval remains authoritative for protected
external effects.

## Consequences

- Product and domain standards can be registered without adding domain branches to
  the core.
- A mandatory requirement cannot be removed by a user prompt, reviewer response, or
  child agent.
- Evidence is owner-scoped through the artifact boundary and becomes stale when its
  protected input changes.
- Offline `EvaluationRunner` remains distinct from runtime quality gates.
