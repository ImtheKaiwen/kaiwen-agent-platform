# ADR 0001: Separate the reusable platform from product applications

- Status: Accepted

## Context

Kaiwen needs the same agent runtime and browser integration in more than one product.
Allowing the first consumer, `kaiwen.com.tr`, to define the package architecture would
couple later products to its database, routes, prompts, tools, and visual language.

## Decision

The Python runtime, shared protocol, and headless UI runtime are independently
published reusable packages. Consuming applications own domain tools, prompts,
authorization composition, HTTP routes, persistence integration, branded components,
and product copy. Reusable packages never import a consuming application, and product
code uses released package APIs instead of copying package source.

## Consequences

- Product capabilities are integrated through explicit ports and registrations.
- A useful feature in one product enters the platform only when it has a genuinely
  product-neutral contract.
- Package releases and product deployments remain separate operations.
