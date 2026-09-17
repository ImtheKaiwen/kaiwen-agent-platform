# Kaiwen Agent Platform

Provider-neutral, reusable agent runtime and UI protocol for Kaiwen products.

This repository intentionally separates the reusable runtime from product-specific
tools, prompts, persistence models, and visual themes.

## Packages

- `backend`: asynchronous Python runtime published as `kaiwen-agent`.
- `packages/protocol`: canonical, versioned JSON Schema and TypeScript contracts.
- `packages/ui-agent`: headless browser runtime and optional React Dynamic Island.
- `examples/basic-agent`: provider-free executable example.

## Install

```bash
pip install "kaiwen-agent[openai]"
npm install @imthekaiwen/agent-protocol @imthekaiwen/agent-ui
```

The project is currently an alpha. Pin exact versions in consuming applications.
Coding agents should start with [`AGENTS.md`](AGENTS.md) and
[`docs/consumer-agent-brief.md`](docs/consumer-agent-brief.md).

## Local development

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

No provider credentials are required for the core test suite or the basic example.

For the optional live smoke test, copy `.env.example` to `.env`, add the API key,
then run:

```powershell
.\backend\.venv\Scripts\python.exe examples\openai-smoke\main.py
```

Current implementation status is tracked in [`docs/roadmap.md`](docs/roadmap.md).
Persistence and event delivery are documented in
[`docs/persistence.md`](docs/persistence.md).
Task graphs, workers, control messages, and scheduling are documented in
[`docs/tasks.md`](docs/tasks.md).
The browser runtime, semantic action boundary, and React bindings are documented
in [`docs/ui-agent.md`](docs/ui-agent.md).
Release registry setup and the protected publishing workflow are documented in
[`docs/releasing.md`](docs/releasing.md).

## Design constraints

- Core code is async and independent of OpenAI, FastAPI, databases, and web frameworks.
- Applications own domain tools and authorization context.
- Every event uses a versioned envelope.
- Tool access is deny-by-default and checked by the runtime.
- Side-effecting tools will gain approval and idempotency middleware before release.
