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

## Working assumptions to preserve

- Provider-specific behavior remains in adapters; core contracts must not expose SDK
  objects. Prefer deterministic fakes and contract tests over live-provider tests.
- SQLite and in-memory implementations are references for local use, not an implicit
  production deployment choice.
- “Implemented” does not authorize publishing, pushing, or deploying. Those are
  explicit release actions and package versions are immutable once published.
- Memory, production scaling, telephony, and scheduled calls are deliberate later
  phases. Follow `docs/roadmap.md`; do not fill gaps with undocumented provider
  behavior or pre-emptively place product policy in reusable packages.
