# AI context

Read `AGENTS.md`, `docs/architecture.md`, and `docs/roadmap.md` before making changes;
then read the subsystem document relevant to the task. ADRs under `docs/decisions/`
record boundaries that must not be changed incidentally. The roadmap is the source of
truth for sequencing and completion status, not this file.

## Repository relationship

- This repository is the reusable **Kaiwen Agent Platform**. `kaiwen.com.tr` is a
  separate consuming application and the first integration target, not the owner of
  the platform architecture.
- Cross-product Python orchestration belongs in `kaiwen-agent`; stable shared wire
  contracts belong in `@imthekaiwen/agent-protocol`; headless browser state,
  transports, and React bindings belong in `@imthekaiwen/agent-ui`.
- Portfolio tools, database models, routes, authentication composition, prompts,
  Turkish copy, branding, page layout, and admin workflows stay in `kaiwen.com.tr`.
  A product feature should move here only after a product-neutral interface exists.
- Consumers should install pinned releases and integrate through public APIs. Do not
  copy this repository's source into a product to bypass packaging.

## Product-direction nuances

- The public portfolio Dynamic Island is a compact visitor-facing demonstration. The
  authenticated admin agent is the long-term operational surface. Do not infer that
  every admin capability, realtime control, or future phone workflow belongs on the
  public homepage.
- Visual behavior is intentionally split: this repository owns headless states and a
  themeable reference component; each product owns final motion, sizing, styling,
  artifacts, and responsive presentation.
- Text and voice should converge on the same durable conversation and task systems.
  Avoid parallel chat, voice, admin, or telephony agent implementations.
- The planned `AgentRuntime` is a compatibility-preserving composition facade over
  the existing `Agent` and runtime services. Simple chat must remain independent of
  task, quality, and team machinery; full side-effecting autonomy follows durable
  action-intent and recovery support, not before it.

## Working assumptions to preserve

- Provider-specific behavior remains in adapters; core contracts must not expose SDK
  objects. Prefer deterministic fakes and contract tests over live-provider tests.
- SQLite and in-memory implementations are references for local use, not an implicit
  production deployment choice.
- “Implemented” does not authorize publishing, pushing, or deploying. Those are
  explicit release actions and package versions are immutable once published.
- Standards describe evidence-backed delivery requirements; they do not grant
  permissions and must remain separate from prompts, policies, skills, and offline
  evaluation.
- Short-term session summaries remain distinct from durable memory. Long-term
  candidate admission, policy-gated recall, and the optional PostgreSQL/pgvector
  adapter now exist, while model-driven extraction, consolidation/decay workers,
  shared-project ACL composition, production scaling, and scheduled calls remain
  later phases. Follow `docs/roadmap.md`; product policy stays in consuming apps.
