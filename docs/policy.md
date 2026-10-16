# Policy engine

The central policy engine evaluates framework-neutral policy rules before an action
crosses an execution boundary. Product applications register their own rules; the
reusable package contains only generic capability, runtime, scheduling, delegation,
and tool adapters.

## Decision precedence

The engine resolves matching decisions in this order:

deny, require approval, review, modify, allow.

No matching policy is denied by default. Tool execution always supplies built-in
permission and approval policies, which preserves the existing tool behavior while
allowing additional product policy to make the result stricter.

## Tool execution order

1. Validate model-generated input.
2. Evaluate tool permissions and registered policy.
3. Revalidate any policy-modified arguments.
4. Resolve approval.
5. Perform idempotency lookup.
6. Execute with timeout and retry.
7. Persist idempotency result and emit audit/events.

A deny decision always wins. A custom policy cannot use allow or modify to bypass a
missing permission or required approval.

## Product composition

Consumers create a PolicyRegistry, register product-neutral policy instances or
product-owned PolicyRule implementations, then inject PolicyEngine into ToolExecutor.
Tenant, user, agent, session, conversation, and run identity must originate from
trusted application context rather than model arguments.

Policy decisions are written through the existing redacting AuditStore and emitted
through canonical policy event types. Product HTTP routes, policy configuration
files, and domain-specific rules remain outside this package.
