# Persistence and event delivery

## Ports

The core exposes four independent persistence boundaries:

- `SessionStore` for application session metadata.
- `RunStore` for lifecycle and completion state.
- `EventStore` for ordered replayable runtime events.
- `AuditStore` for security-relevant execution records.

Applications may use one adapter for all four boundaries or compose separate stores.
The core does not require SQLAlchemy, a web framework, or a specific database.

## SQLite reference adapter

`SQLitePersistence` implements all four boundaries using the Python standard library.
It enables WAL mode, uses a monotonically increasing event sequence, and opens a
short-lived connection for each async operation through `asyncio.to_thread`.

```python
from kaiwen_agent.persistence import SQLitePersistence

persistence = SQLitePersistence("runtime/agent.sqlite3")
agent = Agent(
    name="example",
    model=provider,
    event_sink=persistence,
    run_store=persistence,
)
```

SQLite is the reference and local-development adapter. Multi-instance deployments
should implement the same ports with PostgreSQL or another transactional store.

## SSE

`SSEEventBroker` can persist an event to another sink and fan it out to active
session subscribers. It yields framework-neutral SSE strings, so FastAPI, Starlette,
or another HTTP adapter can wrap the stream without entering the core package.

## Audit redaction

`RedactingAuditStore` recursively removes credential-like keys and common API key or
Bearer token values before forwarding a record. Product applications should still
avoid adding unnecessary personal or secret data to audit details.
