from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from kaiwen_agent.types import utc_now

EventType = Literal[
    "conversation.input",
    "conversation.delta",
    "conversation.completed",
    "run.started",
    "run.status",
    "run.completed",
    "run.failed",
    "tool.started",
    "tool.completed",
    "tool.failed",
    "task.created",
    "task.queued",
    "task.started",
    "task.progress",
    "task.retrying",
    "task.paused",
    "task.resumed",
    "task.completed",
    "task.failed",
    "task.cancelled",
    "resource.waiting",
    "resource.acquired",
    "resource.released",
    "approval.requested",
    "approval.resolved",
    "artifact.created",
    "client.connected",
    "client.capabilities",
    "client.state",
    "client_action.requested",
    "client_action.result",
    "client_action.failed",
]


class AgentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(default_factory=lambda: f"evt_{uuid4().hex}")
    type: EventType
    timestamp: datetime = Field(default_factory=utc_now)
    trace_id: str
    session_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class EventSink(Protocol):
    async def append(self, event: AgentEvent) -> None: ...


class EventStore(EventSink, Protocol):
    async def list_events(
        self,
        *,
        session_id: str,
        after_id: str | None = None,
        limit: int = 100,
    ) -> list[AgentEvent]: ...


class InMemoryEventSink:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    async def append(self, event: AgentEvent) -> None:
        self.events.append(event)

    async def list_events(
        self,
        *,
        session_id: str,
        after_id: str | None = None,
        limit: int = 100,
    ) -> list[AgentEvent]:
        events = [event for event in self.events if event.session_id == session_id]
        if after_id is not None:
            index = next(
                (index for index, event in enumerate(events) if event.id == after_id),
                len(events),
            )
            events = events[index + 1 :]
        return [event.model_copy(deep=True) for event in events[:limit]]
