# Ecosystem integration boundaries

The platform exposes small, optional ports for filesystem and MCP integrations. They
do not make external capabilities trusted and do not replace the central tool safety
pipeline.

## Workspace filesystem

`WorkspaceFilesystem` is configured by the host with a trusted workspace ID and one
or more named absolute roots. Tool arguments contain only a root name and a relative
path. Paths are canonicalized before access; absolute paths, traversal outside a
root, and symlink escapes are rejected. Reads and writes have independent byte
limits. Writes are atomic, require the `workspace.write` permission and approval,
and do not create missing parent directories.

The workspace ID comes from trusted `AgentContext` metadata. A model cannot select a
different workspace by adding an argument. Hosts should still use operating-system or
container isolation when untrusted local processes can concurrently modify symlinks;
the adapter is not a replacement for a sandbox.

Deletion and unrestricted shell execution are intentionally absent.

## MCP tools

MCP discovery is descriptive, not authorization. `bind_mcp_tool` requires a host to
provide a trusted Pydantic input model, permissions, side-effect classification, and
approval requirement. The discovered descriptor schema must exactly match that model
before a `ToolDefinition` is created.

The resulting tool runs through `ToolExecutor`, so normal validation, policy,
approval, idempotency, timeout, audit, and lifecycle behavior still applies. Remote
MCP output remains untrusted data. Product-specific MCP registrations and permissions
belong in the consuming application.
