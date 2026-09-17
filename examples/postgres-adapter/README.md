# PostgreSQL adapter outline

Production applications can implement the framework ports with their preferred async
PostgreSQL driver. Keep database-specific connection pools outside the core:

```python
class PostgresEventStore:
    def __init__(self, pool):
        self.pool = pool

    async def append(self, event):
        await self.pool.execute(
            """
            INSERT INTO agent_events
                (id, type, timestamp, trace_id, session_id, payload)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """,
            event.id,
            event.type,
            event.timestamp,
            event.trace_id,
            event.session_id,
            event.payload,
        )

    async def list_events(self, *, session_id, after_id=None, limit=100):
        # Resolve `after_id` to its BIGSERIAL sequence and return rows in ASC order.
        ...
```

Recommended tables mirror the SQLite reference adapter:

- `agent_sessions`
- `agent_runs`
- `agent_events` with `BIGSERIAL sequence`
- `agent_audit_log` with `BIGSERIAL sequence`

Index events by `(session_id, sequence)` and audit records by `(trace_id, sequence)`.
Use JSONB for metadata and payloads. Application migrations own retention policies,
partitioning, encryption, and tenant isolation.
