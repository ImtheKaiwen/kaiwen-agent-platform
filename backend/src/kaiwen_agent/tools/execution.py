from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from pydantic import ValidationError

from kaiwen_agent.audit import AuditRecord, AuditStore, RedactingAuditStore, SecretRedactor
from kaiwen_agent.context import AgentContext
from kaiwen_agent.events import EventType
from kaiwen_agent.exceptions import (
    ApprovalDeniedError,
    ApprovalRequiredError,
    PermissionDeniedError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolValidationError,
)
from kaiwen_agent.tools.approval import ApprovalGate, ApprovalRequest
from kaiwen_agent.tools.definition import ToolDefinition
from kaiwen_agent.tools.idempotency import IdempotencyStore, InMemoryIdempotencyStore
from kaiwen_agent.types import ToolCall, ToolResult

ToolEventCallback = Callable[[EventType, dict[str, object]], Awaitable[None]]


async def _no_events(event_type: EventType, payload: dict[str, object]) -> None:
    del event_type, payload


class ToolExecutor:
    def __init__(
        self,
        *,
        approval_gate: ApprovalGate | None = None,
        idempotency_store: IdempotencyStore | None = None,
        audit_store: AuditStore | None = None,
        redactor: SecretRedactor | None = None,
    ) -> None:
        self.approval_gate = approval_gate
        self.idempotency_store = idempotency_store or InMemoryIdempotencyStore()
        self.audit_store = (
            RedactingAuditStore(audit_store, redactor) if audit_store is not None else None
        )

    async def execute(
        self,
        definition: ToolDefinition,
        call: ToolCall,
        context: AgentContext,
        *,
        execution_scope: str,
        emit: ToolEventCallback = _no_events,
    ) -> ToolResult:
        try:
            arguments = definition.input_model.model_validate(call.arguments)
        except ValidationError as error:
            await self._audit(
                context,
                definition,
                call,
                "failed",
                {"error_type": type(error).__name__, "arguments": call.arguments},
            )
            raise ToolValidationError(f"Invalid arguments for {definition.name}") from error

        missing = definition.permissions - context.permissions
        if missing:
            required = ", ".join(sorted(missing))
            await self._audit(
                context,
                definition,
                call,
                "denied",
                {"missing_permissions": sorted(missing)},
            )
            raise PermissionDeniedError(f"Tool {definition.name} requires: {required}")

        if definition.requires_approval:
            request = ApprovalRequest(
                tool_name=definition.name,
                call_id=call.id,
                arguments=call.arguments,
                side_effect=definition.side_effect,
            )
            await emit("approval.requested", {"tool": definition.name, "call_id": call.id})
            if self.approval_gate is None:
                await self._audit(
                    context, definition, call, "denied", {"reason": "approval_unavailable"}
                )
                raise ApprovalRequiredError(f"Tool {definition.name} requires approval")
            approved = await self.approval_gate.approve(request, context)
            await emit(
                "approval.resolved",
                {"tool": definition.name, "call_id": call.id, "approved": approved},
            )
            if not approved:
                await self._audit(
                    context, definition, call, "denied", {"reason": "approval_denied"}
                )
                raise ApprovalDeniedError(f"Approval denied for tool {definition.name}")

        idempotency_key = call.idempotency_key
        if definition.side_effect != "none" and idempotency_key is None:
            idempotency_key = f"{execution_scope}:{call.id}"
        if idempotency_key is not None:
            idempotency_key = f"{definition.name}:{idempotency_key}"
            cached = await self.idempotency_store.get(idempotency_key)
            if cached is not None:
                await self._audit(
                    context, definition, call, "succeeded", {"cached": True}
                )
                await emit(
                    "tool.completed",
                    {"tool": definition.name, "call_id": call.id, "cached": True},
                )
                return cached.model_copy(update={"call_id": call.id})

        await emit("tool.started", {"tool": definition.name, "call_id": call.id})
        last_error: BaseException | None = None
        for attempt in range(1, definition.retry_policy.max_attempts + 1):
            try:
                output: Any = await asyncio.wait_for(
                    definition.handler(context, arguments),
                    timeout=definition.timeout_seconds,
                )
                result = ToolResult(call_id=call.id, name=definition.name, output=output)
                if idempotency_key is not None:
                    await self.idempotency_store.put(idempotency_key, result)
                await self._audit(
                    context,
                    definition,
                    call,
                    "succeeded",
                    {"attempt": attempt, "cached": False},
                )
                await emit(
                    "tool.completed",
                    {
                        "tool": definition.name,
                        "call_id": call.id,
                        "attempt": attempt,
                        "cached": False,
                    },
                )
                return result
            except TimeoutError:
                last_error = ToolTimeoutError(
                    f"Tool {definition.name} timed out after {definition.timeout_seconds}s"
                )
                retryable = TimeoutError in definition.retry_policy.retry_on
            except Exception as error:
                last_error = error
                retryable = isinstance(error, definition.retry_policy.retry_on)

            if attempt < definition.retry_policy.max_attempts and retryable:
                if definition.retry_policy.backoff_seconds:
                    await asyncio.sleep(definition.retry_policy.backoff_seconds)
                continue
            break

        await emit(
            "tool.failed",
            {
                "tool": definition.name,
                "call_id": call.id,
                "error_type": type(last_error).__name__,
            },
        )
        await self._audit(
            context,
            definition,
            call,
            "failed",
            {"error_type": type(last_error).__name__},
        )
        if isinstance(last_error, ToolTimeoutError):
            raise last_error
        raise ToolExecutionError(f"Tool {definition.name} failed") from last_error

    async def _audit(
        self,
        context: AgentContext,
        definition: ToolDefinition,
        call: ToolCall,
        outcome: Literal["succeeded", "failed", "denied"],
        details: dict[str, object],
    ) -> None:
        if self.audit_store is None:
            return
        await self.audit_store.append_audit(
            AuditRecord(
                trace_id=context.trace_id or "trace_unavailable",
                session_id=context.session_id,
                action=f"tool:{definition.name}",
                outcome=outcome,
                details={
                    "call_id": call.id,
                    "side_effect": definition.side_effect,
                    "arguments": call.arguments,
                    **details,
                },
            )
        )


async def execute_tool(
    definition: ToolDefinition,
    call: ToolCall,
    context: AgentContext,
) -> ToolResult:
    """Compatibility helper for the default, non-approval execution path."""

    return await ToolExecutor().execute(
        definition,
        call,
        context,
        execution_scope="standalone",
    )
