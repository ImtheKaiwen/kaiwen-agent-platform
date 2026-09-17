from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentContext:
    session_id: str
    trace_id: str | None = None
    permissions: frozenset[str] = field(default_factory=frozenset)
    services: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
