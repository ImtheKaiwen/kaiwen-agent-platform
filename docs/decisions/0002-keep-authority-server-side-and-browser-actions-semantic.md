# ADR 0002: Keep authority server-side and browser actions semantic

- Status: Accepted

## Context

An agent can request tool execution and UI changes, but model output and browser code
are not trusted authorization boundaries. Passing executable code, selectors, or
unrestricted action names to the browser would make product behavior unsafe and hard
to keep compatible.

## Decision

The backend is the decision authority for identity, permissions, approvals, tools,
side effects, and provider credentials. Browser behavior is exposed only through
versioned, schema-validated semantic actions explicitly registered by the host
application. Unknown tools and actions are denied by default. Client allowlisting is
an additional safety boundary and never replaces server authorization.

## Consequences

- API keys and provider SDK calls cannot move into browser packages.
- Navigation, modals, form prefilling, and similar behavior use stable intent-level
  contracts rather than DOM implementation details.
- Adding or changing an action requires coordinated protocol, server policy, host
  registration, and contract-test updates.
