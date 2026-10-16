# Context engine and short-term memory

Context building and memory are separate concerns.

- ContextBuilder assembles bounded model context for one request.
- ConversationStore remains the durable source of normalized text and voice messages.
- SessionMemoryManager stores only a compact, expiring session summary.
- Task and job progress do not belong in memory.

## Context sources

The first implementation includes current input, static system or policy content,
recent conversation, and session summary sources. Future task, job, objective,
knowledge, and long-term memory sources implement the same ContextSource protocol.

Every source has a type-specific token budget and the complete context has a hard
total budget. Required and higher-priority content is allocated first. Optional
source failures are recorded as omitted; required source failures stop the build.

Recent conversation retrieval verifies tenant, conversation, and user identity.
Conversation IDs supplied by a client are not sufficient on their own.

## Session summaries

SessionSummary is structured and tenant/user/conversation scoped. The manager:

- enforces a maximum estimated token count;
- applies an explicit retention period;
- discards expired summaries on read;
- supports deterministic forget;
- does not call a model or infer durable preferences.

In-memory and SQLite stores are reference implementations. Model-generated
summarization, sensitive-data admission, long-term memory, conflict handling, and
semantic retrieval are deliberately deferred to the long-term memory phase.
