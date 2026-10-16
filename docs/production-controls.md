# Evaluation, replay, and production controls

These APIs are product-neutral building blocks. They do not silently attach to a
consumer's runtime; the host composes them with its policy, persistence, scheduler,
and admin surfaces.

## Evaluation and simulation

`EvaluationRunner` executes structured, versioned cases against an injected target
and evaluates data paths with declarative assertions. Suites cover safety and runtime
behavior without embedding product prompts or fixtures in the package. Simulation is
the default.

`ReplayRecorder` stores canonical events in trace order and `ReplayPlayer` delivers
them only to an observer. Replay never invokes a tool. A host that performs what-if
agent runs must register `SimulationSideEffectPolicy` in the central policy engine
and use `environment="simulation"`; reversible/destructive tools and explicitly
marked external writes then fail closed. In-memory and restart-safe SQLite replay
stores are included as references.

## Dead-letter queue

`DeadLetterManager` accepts exhausted event, job, task, watch, and webhook failures.
Payloads are size-bounded and secret-redacted before persistence. Reads and state
changes are tenant/user scoped, and requeue marking is single-use; actual retry
execution remains an explicit host action. In-memory and SQLite stores are provided.

## Backpressure

`BackpressureController` provides tenant-scoped queue-depth, concurrency, rolling
rate, resource-capacity, and low-priority admission decisions. Successful admission
returns a lease that must be released. The reference controller is process-local;
distributed queue-depth and rate accounting still require a production adapter.

## Distributed coordination

`LeaseStore` is the provider-neutral coordination boundary for exclusive scheduler,
worker, trigger, and maintenance ownership. `InMemoryLeaseStore` is deterministic
test support. `RedisLeaseStore` uses atomic Lua operations, opaque random ownership
tokens, expiring leases, and monotonically increasing fencing tokens so a stale
owner cannot renew or release a successor's lease. Raw resource names are hashed
before becoming Redis keys. Redis support is optional through
`kaiwen-agent[redis]`.

Consumers must propagate and validate the fencing token at the protected durable
resource; a Redis lease alone cannot prevent a paused stale process from writing
after its lease expires. The lease adapter coordinates ownership, but it is not a
distributed rate limiter and does not make the process-local backpressure counters
global.

SQLite budget reservations use one `BEGIN IMMEDIATE` transaction across all
applicable scopes. This prevents check/write races among local workers sharing one
database. Multi-node deployments still need a store whose `reserve` operation is
atomic at the deployment's database boundary.

## Heartbeats and health

`HeartbeatMonitor` tracks named components such as the scheduler, job supervisor,
workers, event consumers, realtime manager, and watch engine. Reports derive
healthy, degraded, offline, or unknown status from monotonic heartbeat timestamps and
configured thresholds. Deployment-specific probes and alerts remain host-owned.

## Metrics

`RuntimeMetrics` records a fixed catalog of lifecycle, job, policy, memory, context,
model-cost, watch, objective, and queue metrics through an injected `MetricsSink`.
Every record carries trusted tenant, agent, and trace identity plus optional run,
job, and cycle IDs. Callers cannot attach arbitrary labels, which prevents accidental
secret capture and unbounded label cardinality. The bounded in-memory sink is for
tests and local development; production exporters implement the same sink protocol
and own aggregation, retention, dashboards, and alerts.

## Secrets

`SecretProvider` is the adapter boundary for credentials. The environment adapter
requires an explicit key allowlist and returns an opaque `SecretValue` whose repr and
serialization mask plaintext. Plaintext is available only through the explicit
`reveal()` call at the provider integration boundary. Audit redaction also recognizes
Pydantic secret values. Vault and cloud adapters can implement the same protocol.
