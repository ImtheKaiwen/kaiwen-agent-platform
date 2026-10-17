# Built-in tool adapters

The adapters in `kaiwen_agent.toolkits` are optional definitions for the existing
central `ToolExecutor`. Importing them does not register a tool, inspect a repository,
or grant a permission. The host constructs an adapter with trusted workspace and
identity bindings, registers selected `ToolDefinition` objects, and supplies the
matching permissions through its normal policy composition.

## Read-only workspace tools

| Tool | Permission | Behavior |
|---|---|---|
| `workspace.list_files` | `workspace.read` | Bounded depth/count listing; skips configured caches, generated directories, `.env`, and common private-key files. |
| `workspace.stat` | `workspace.read` | File type, size, and bounded SHA-256 checksum. |
| `workspace.read_lines` | `workspace.read` | At most 1,000 requested UTF-8 lines. |
| `workspace.read_batch` | `workspace.read` | At most twenty bounded line-range reads. |
| `workspace.search_text` | `workspace.read` | Bounded literal or restricted-regex search with capped files, matches, line length, and previews. |

These extend `WorkspaceFilesystem`; they do not add another path resolver. Absolute
paths, traversal, symlink escapes, wrong workspace IDs, and configured tenant/user
mismatches fail closed. The original `workspace.read_text` and
`workspace.write_text` remain backward-compatible.

The restricted regular-expression mode rejects lookarounds, backreferences, repeated
quantifiers, and nested quantified groups. It is intended for bounded source search,
not arbitrary PCRE execution.

## Read-only Git tools

`ReadOnlyGitRepository` binds one allowlisted workspace root containing a local Git
repository and exposes:

- `git.status`
- `git.diff`
- `git.log`
- `git.show`

Every invocation uses a fixed executable and argument construction with
`shell=False`, disabled external diff helpers, disabled terminal prompting, a
minimal secret-free environment, timeout, and output caps. Revisions and paths are
validated before use. These tools have side-effect class `none` and permission
`git.read`; no commit, push, checkout, reset, clean, fetch, or remote operation is
included in the read-only kit.

## Project detection

`project.detect` reads only a fixed manifest catalog and emits a typed
`ProjectSnapshot` with manifest checksums, detected languages/frameworks/package
managers, explicit boolean or unknown applicability facts, and suggested check IDs.
Suggested checks are descriptive and never authorize process execution.

## Tool bundles

`ToolBundleDefinition` is an immutable versioned collection of tool names. Selecting
a bundle never grants permissions. Effective access remains the intersection of the
registered tools, agent definition, capability manifest, workspace allowlist,
trusted caller permissions, central policy, and approval controls.

## Current boundary

## CK2 write and command adapters

`workspace.apply_patch` accepts one bounded unified diff and an exact SHA-256
preimage. It applies the diff in-process, rejects stale or mismatched hunks, writes
atomically through `WorkspaceFilesystem`, requires `workspace.write`, and requires
central approval. `workspace.mkdir` creates one directory under an existing parent
with the same permission and approval boundary. Neither tool deletes files.

Process execution uses a host-authored `CommandCatalog`:

- the model selects only a registered command ID and typed parameter values;
- presets define the exact executable, argv template, category, workspace-relative
  directory, timeout, output cap, network setting, and workspace write setting;
- parameters occupy whole argv tokens and pass host-authored validation;
- no shell string, pipeline, redirection, environment expansion, or arbitrary
  working directory is accepted;
- returned output is size-checked and secret-redacted before model exposure.

`commands.run_allowed` requires `commands.execute` and approval. Category-scoped
`testing.run`, `quality.lint`, `quality.typecheck`, and `build.run` use the same
catalog and can omit per-call approval only when the host deliberately configures a
validated isolated runner and policy.

The package includes `FakeSandboxRunner` for deterministic contract tests and
`UnsupportedSandboxRunner` for fail-closed hosts. It does **not** currently claim a
validated built-in OS/container runner. Real process execution, process-tree cleanup,
CPU/memory limits, network isolation, and package lifecycle-hook containment remain
the responsibility of an injected host sandbox adapter until one is separately
implemented and validated. The toolkit never falls back to unrestricted host
subprocess execution.

There is still no delete operation, unrestricted shell, package installer, remote
Git operation, network client, deployment, or publication tool. Tool handlers must
not be invoked directly to bypass `ToolExecutor`.
