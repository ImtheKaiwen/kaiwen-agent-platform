from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from kaiwen_agent.context import AgentContext
from kaiwen_agent.tools.definition import ToolDefinition


class WorkspacePathError(PermissionError):
    pass


class WorkspaceFilesystem:
    """Bounded filesystem adapter for one host-authorized workspace."""

    def __init__(
        self,
        *,
        workspace_id: str,
        roots: dict[str, Path],
        max_read_bytes: int = 1_000_000,
        max_write_bytes: int = 1_000_000,
    ) -> None:
        if not workspace_id or not roots:
            raise ValueError("workspace_id and roots are required")
        if any(not name for name in roots):
            raise ValueError("Workspace root names cannot be empty")
        self.workspace_id = workspace_id
        self.roots = {name: path.resolve(strict=True) for name, path in roots.items()}
        if any(not path.is_dir() for path in self.roots.values()):
            raise ValueError("Workspace roots must be directories")
        if max_read_bytes < 1 or max_write_bytes < 1:
            raise ValueError("Filesystem limits must be positive")
        self.max_read_bytes = max_read_bytes
        self.max_write_bytes = max_write_bytes

    def read_text(self, root: str, relative_path: str) -> str:
        path = self._resolve(root, relative_path, must_exist=True)
        if not path.is_file():
            raise WorkspacePathError("Workspace path is not a file")
        if path.stat().st_size > self.max_read_bytes:
            raise ValueError("Workspace read exceeds the configured byte limit")
        return path.read_text(encoding="utf-8")

    def write_text(self, root: str, relative_path: str, content: str) -> int:
        encoded = content.encode()
        if len(encoded) > self.max_write_bytes:
            raise ValueError("Workspace write exceeds the configured byte limit")
        path = self._resolve(root, relative_path, must_exist=False)
        if not path.parent.is_dir():
            raise WorkspacePathError("Workspace parent directory does not exist")
        handle, temporary = tempfile.mkstemp(prefix=".kaiwen-", dir=path.parent)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
        return len(encoded)

    def _resolve(self, root: str, relative_path: str, *, must_exist: bool) -> Path:
        try:
            base = self.roots[root]
        except KeyError as error:
            raise WorkspacePathError("Workspace root is not allowlisted") from error
        supplied = Path(relative_path)
        if supplied.is_absolute() or not relative_path or "\x00" in relative_path:
            raise WorkspacePathError("Workspace path must be relative")
        try:
            candidate = (base / supplied).resolve(strict=False)
        except (OSError, RuntimeError) as error:
            raise WorkspacePathError("Workspace path cannot be resolved") from error
        if not candidate.is_relative_to(base):
            raise WorkspacePathError("Workspace path escapes its allowlisted root")
        if must_exist and not candidate.exists():
            raise WorkspacePathError("Workspace path does not exist")
        return candidate


class WorkspaceReadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=2_000)


class WorkspaceWriteInput(WorkspaceReadInput):
    content: str


def workspace_tools(filesystem: WorkspaceFilesystem) -> tuple[ToolDefinition, ToolDefinition]:
    async def read(context: AgentContext, arguments: BaseModel):
        if not isinstance(arguments, WorkspaceReadInput):
            raise TypeError("Workspace read arguments were not validated")
        _require_workspace(context, filesystem.workspace_id)
        return {"content": filesystem.read_text(arguments.root, arguments.path)}

    async def write(context: AgentContext, arguments: BaseModel):
        if not isinstance(arguments, WorkspaceWriteInput):
            raise TypeError("Workspace write arguments were not validated")
        _require_workspace(context, filesystem.workspace_id)
        size = filesystem.write_text(arguments.root, arguments.path, arguments.content)
        return {"bytes_written": size}

    return (
        ToolDefinition(
            name="workspace.read_text",
            description="Read a UTF-8 file inside an allowlisted workspace root.",
            input_model=WorkspaceReadInput,
            handler=read,
            permissions=frozenset({"workspace.read"}),
        ),
        ToolDefinition(
            name="workspace.write_text",
            description="Atomically write UTF-8 content inside an allowlisted workspace root.",
            input_model=WorkspaceWriteInput,
            handler=write,
            permissions=frozenset({"workspace.write"}),
            side_effect="reversible",
            requires_approval=True,
        ),
    )


def _require_workspace(context: AgentContext, workspace_id: str) -> None:
    if context.metadata.get("workspace_id") != workspace_id:
        raise WorkspacePathError("Agent context is not bound to this workspace")
