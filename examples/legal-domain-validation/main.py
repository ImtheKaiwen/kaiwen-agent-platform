from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from kaiwen_agent import AgentContext, tool
from kaiwen_agent.exceptions import ApprovalDeniedError
from kaiwen_agent.integrations import WorkspaceFilesystem, WorkspacePathError
from kaiwen_agent.tools.approval import StaticApprovalGate
from kaiwen_agent.tools.execution import ToolExecutor
from kaiwen_agent.types import ToolCall


class SendInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient: str = Field(min_length=3)
    summary: str = Field(min_length=1)


async def validate(workspace: Path) -> dict[str, object]:
    allowed = workspace / "allowed"
    private = workspace / "private"
    allowed.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    (allowed / "policy.txt").write_text(
        "The fictional Acme policy requires human approval before external disclosure.",
        encoding="utf-8",
    )
    (private / "client.txt").write_text("fictional private client data", encoding="utf-8")

    filesystem = WorkspaceFilesystem(
        workspace_id="legal-validation",
        roots={"approved_documents": allowed},
    )
    source = filesystem.read_text("approved_documents", "policy.txt")
    summary = {
        "text": "External disclosure requires human approval.",
        "sources": ["approved_documents/policy.txt"],
    }
    assert "human approval" in source

    isolation_enforced = False
    try:
        filesystem.read_text("approved_documents", "../private/client.txt")
    except WorkspacePathError:
        isolation_enforced = True

    executions = 0

    @tool(
        name="legal.send_external",
        description="Send a legal-domain summary outside the workspace",
        input_model=SendInput,
        permissions={"legal.send"},
        side_effect="destructive",
        requires_approval=True,
    )
    async def send_external(context: AgentContext, arguments: SendInput) -> str:
        nonlocal executions
        del context, arguments
        executions += 1
        return "sent"

    approval_blocked = False
    try:
        await ToolExecutor(approval_gate=StaticApprovalGate(False)).execute(
            send_external,
            ToolCall(
                id="send-1",
                name="legal.send_external",
                arguments={
                    "recipient": "reviewer@example.invalid",
                    "summary": summary["text"],
                },
            ),
            AgentContext(
                session_id="legal-validation",
                tenant_id="validation",
                user_id="researcher",
                permissions=frozenset({"legal.send"}),
            ),
            execution_scope="legal-validation-run",
        )
    except ApprovalDeniedError:
        approval_blocked = True

    if not isolation_enforced or not approval_blocked or executions:
        raise RuntimeError("Legal-domain safety validation failed")
    return {
        "status": "completed",
        "source_references": summary["sources"],
        "document_isolation": isolation_enforced,
        "external_action_blocked": approval_blocked,
        "external_action_executions": executions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(validate(args.workspace.resolve())), sort_keys=True))


if __name__ == "__main__":
    main()
