from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from kaiwen_agent.context import AgentContext


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    tool_name: str
    call_id: str
    arguments: dict[str, Any]
    side_effect: Literal["none", "reversible", "destructive"]


class ApprovalGate(Protocol):
    async def approve(self, request: ApprovalRequest, context: AgentContext) -> bool: ...


class StaticApprovalGate:
    """Explicit approval gate for tests, CLIs, and trusted application adapters."""

    def __init__(self, approved: bool) -> None:
        self.approved = approved

    async def approve(self, request: ApprovalRequest, context: AgentContext) -> bool:
        del request, context
        return self.approved
