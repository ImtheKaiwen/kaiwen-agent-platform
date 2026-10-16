# Long-term memory

Long-term memory stores durable user or project facts separately from conversation
summaries, task progress, and knowledge/RAG documents. The reusable package owns the
admission and storage contracts; consuming products own candidate extraction,
product-specific policy rules, HTTP routes, and final administration UI.

## Safety pipeline

`LongTermMemoryManager.remember()` applies this order:

1. validate the requested namespace against trusted host identity and capabilities;
2. reject credentials and explicit secret sensitivity locally;
3. score the candidate for auto-save, review, or discard;
4. evaluate the central policy engine through `PolicyMemoryAuthorizer`;
5. detect exact duplicates and same-key conflicts;
6. embed only non-secret content that is approved for active storage;
7. persist the memory or place it in the review inbox.

Tenant and user identity are carried by `MemoryOperationContext`, not by
`MemoryCandidate`, so model-generated arguments cannot select their owner. Every
store operation filters by both identifiers. User namespaces are available by
default. Tenant, project, and system namespaces additionally require explicit
capabilities.

Sensitive memories remain `pending_review` and are not embedded. Approving a
replacement atomically activates it and marks the former same-key memory as
`superseded`. Forget is a soft deletion that removes the content, structured data,
and embedding. Consumers may additionally apply physical deletion according to
their retention policy.

## Retrieval

Retrieval is bounded to 50 results and combines lexical similarity, vector
similarity, importance, and confidence. Expired, deleted, disputed, pending, and
superseded records are excluded. `LongTermMemorySource` exposes authorized results
to the bounded context engine.

The in-memory store is deterministic and intended for tests. Production deployments
can install `kaiwen-agent[postgres-memory]` and use `PostgreSQLMemoryStore`, which
uses PostgreSQL full-text search plus pgvector cosine distance. Open and close the
adapter explicitly (or use it as an async context manager); no connection is opened
at import time.

```python
from kaiwen_agent.persistence import PostgreSQLMemoryStore

async with PostgreSQLMemoryStore(
    database_url,
    embedding_dimensions=1536,
) as store:
    ...
```

The database role needs permission to create the `vector` extension during initial
setup. In stricter environments, provision the extension and schema through the
host's migration system before starting the adapter.

## Administration contract

`MemoryAdminService` provides policy-checked overview, review, edit, and forget
operations. It deliberately exposes no web framework or visual styling. Products
must authenticate administrators, construct trusted contexts, and render their own
memory pages.

Long-term candidate extraction and consolidation are intentionally not hidden model
loops. A host can submit explicit candidates now and later run extraction or
consolidation as observable jobs.
