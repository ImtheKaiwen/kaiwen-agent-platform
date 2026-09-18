from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from kaiwen_agent.types import utc_now


class RealtimeEventDelivery(StrEnum):
    EPHEMERAL = "ephemeral"
    DURABLE = "durable"


class RealtimeEventType(StrEnum):
    SESSION_CREATED = "realtime.session.created"
    SESSION_CONNECTING = "realtime.session.connecting"
    SESSION_CONNECTED = "realtime.session.connected"
    SESSION_INTERRUPTED = "realtime.session.interrupted"
    SESSION_RECONNECTING = "realtime.session.reconnecting"
    SESSION_DISCONNECTED = "realtime.session.disconnected"
    SESSION_FAILED = "realtime.session.failed"
    TURN_STARTED = "realtime.turn.started"
    TURN_COMPLETED = "realtime.turn.completed"
    TRANSCRIPT_DELTA = "realtime.transcript.delta"
    TRANSCRIPT_COMPLETED = "realtime.transcript.completed"
    AUDIO_OUTPUT = "realtime.audio.output"
    USAGE_UPDATED = "realtime.usage.updated"
    ERROR = "realtime.error"


class RealtimeProviderEvent(BaseModel):
    """Provider-neutral event local to one realtime connection."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"rtevt_{uuid4().hex}")
    type: RealtimeEventType
    delivery: RealtimeEventDelivery = RealtimeEventDelivery.EPHEMERAL
    timestamp: datetime = Field(default_factory=utc_now)
    provider_event_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class RealtimeRuntimeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"rtevt_{uuid4().hex}")
    type: RealtimeEventType
    delivery: RealtimeEventDelivery = RealtimeEventDelivery.DURABLE
    timestamp: datetime = Field(default_factory=utc_now)
    session_id: str
    conversation_id: str
    tenant_id: str
    user_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
