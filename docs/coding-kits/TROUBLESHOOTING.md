# Coding Kits troubleshooting

- `provider_not_registered`: register a server-side provider factory.
- `model_tool_unsupported`: choose a tool-capable model or use chat only.
- `structured_plan_unsupported`: choose a validated structured-output model or a
  host-approved plan template.
- `locality_violation`: use a registered local provider such as a compatible Ollama
  model; cloud routing is not allowed.
- `tool_not_registered`: register the exact first-party/host tool before composition.
- `approval_required`: resolve the exact pending call; approvals are one-time scoped.
- `sandbox_missing`: inject a real bounded sandbox; the package does not execute host
  processes by default.
- stale evidence or patch: rediscover/retest against the current fingerprint rather
  than weakening the checksum.

Migration from direct `AgentRuntime` is optional: keep existing code or create a
`CodingKitFactory` around the same registries. Root imports and baseline chat remain
unchanged.
