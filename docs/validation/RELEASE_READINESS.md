# Release readiness

## Decision

**Technically ready for versioning and explicit publication approval.** There are no
known critical or high-severity runtime failures, the bounded live OpenAI check passes,
and GitHub CI run `38996229262` is green for both Python and Node jobs. Public package
publication has not been started.

## Mandatory before release

1. Align release metadata. PyPI currently publishes `kaiwen-agent 0.4.0a1`, while the
   latest Git tag/GitHub Release remains `v0.3.0a1`.
2. Choose and apply versions before dispatching the release workflow. Recommended:
   Python `0.5.0a1` for the substantial additive runtime APIs, and npm
   `0.2.0-alpha.1` for the additive protocol/UI changes.
3. Review the low-severity development-only `esbuild` advisory. A forced upgrade is
   not recommended until the project raises its Node support floor enough for the
   fixed `tsup` major, or an upstream compatible release becomes available.

Gemini, Ollama, PostgreSQL, Redis, real media, and telephony provider checks are
optional-provider validation gaps. They block claims about those deployments, but do
not block an alpha release if release notes state the limitation.

## Release artifacts

- PyPI: `kaiwen-agent`
- npm: `@imthekaiwen/agent-protocol`
- npm: `@imthekaiwen/agent-ui`

The repository's `release.yml` verifies Python and Node checks before publishing and
uses PyPI trusted publishing plus npm provenance. The workflow now also runs formatter
checks and the isolated Todo/legal validations.

## Post-publish verification

After explicit approval and workflow completion:

1. create a new empty virtual environment;
2. install the exact PyPI version;
3. run minimal, autonomous, team, and consumer smoke tests;
4. install both exact npm versions into a clean consumer project;
5. build/typecheck that project;
6. confirm PyPI, npm, Git tag, GitHub Release, and changelog versions match.
