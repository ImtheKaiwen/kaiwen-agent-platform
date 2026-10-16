# Context engine and short-term memory

Context building and memory are separate concerns.

- ContextBuilder assembles bounded model context for one request.
- ConversationStore remains the durable source of normalized text and voice messages.
- SessionMemoryManager stores only a compact, expiring session summary.
- Task and job progress do not belong in memory.

`AgentRuntime` can now receive an optional `ContextBuilder`, bounded
`ContextBudget`/`ContextWindow`, and `ContextCompactionManager`. Without those ports,
the chat fast path and legacy `Agent` behavior remain unchanged.

## Context sources

The first implementation includes current input, static system or policy content,
recent conversation, and session summary sources. Future task, job, objective,
knowledge, and long-term memory sources implement the same ContextSource protocol.

Every source has a type-specific token budget and the complete context has a hard
total budget. Required and higher-priority content is allocated first. Optional
source failures are recorded as omitted; required source failures stop the build.

Token accounting uses an injected `TokenCounter`. The dependency-free fallback keeps
the original estimate, while provider adapters can supply a tokenizer through
`CallableTokenCounter`. Output reservations, fixed request overhead, and selected tool
schemas reduce the available input window before the provider is called. Overflow
fails before a model request rather than silently dropping required authority.

Recent conversation retrieval verifies tenant, conversation, and user identity.
Conversation IDs supplied by a client are not sufficient on their own.

## Session summaries

SessionSummary is structured and tenant/user/conversation scoped. The manager:

- enforces a maximum estimated token count;
- applies an explicit retention period;
- discards expired summaries on read;
- supports deterministic forget;
- does not call a model or infer durable preferences.

Automatic rolling compaction is a separate injected service. It calls a host-owned
structured `SummaryGenerator` only after a soft threshold, keeps recent raw messages,
validates exact source-message provenance, preserves previous goals, decisions,
constraints and artifact references, rejects detected credentials, and leaves raw
conversation history untouched. Missing source cursors fail closed. Canonical prompts,
policy, task state, acceptance criteria, and permissions never come from this lossy
summary.

Large tool output may be passed through `ArtifactToolResultProcessor`. It writes the
full JSON output to an owner-scoped `ArtifactManager` and gives the model only a small
preview plus reference, checksum, size, and MIME metadata. Missing owner scope fails
closed. This is composed as a `ToolExecutor` decorator so the legacy `Agent` public
signature remains unchanged.

In-memory and SQLite stores are reference implementations. Model-generated
summarization, sensitive-data admission, long-term memory, conflict handling, and
semantic retrieval are deliberately deferred to the long-term memory phase.
