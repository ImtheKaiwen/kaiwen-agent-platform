# Permissions and sandbox boundary

Tool bundles are names, not grants. Effective authority is the intersection of the
agent definition, capability manifest, workspace profile, trusted identity, policy,
approval state and host runtime controls.

- Inspection requires `workspace.read` or `git.read`.
- Patches and directory creation require `workspace.write` and approval.
- Command tools accept only host-authored presets and whole-token parameters.
- Command execution requires an injected `SandboxRunner`; the default unsupported
  runner fails closed.
- Reviewers are read-only by default. Tester or DevOps writes need explicit grants.
- A denied, expired or unrelated approval never authorizes another call.
- Workspace roots and tenant/user identities come from trusted host state.

Never implement a convenience fallback using `shell=True`, concatenate model text
into commands, forward `.env` content, or treat a selected bundle as permission.
