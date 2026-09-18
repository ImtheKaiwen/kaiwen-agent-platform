from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from kaiwen_agent.audit import AuditRecord
from kaiwen_agent.control.checkpoints import TaskCheckpoint
from kaiwen_agent.events import AgentEvent
from kaiwen_agent.realtime.conversation import ConversationMessage
from kaiwen_agent.sessions import SessionRecord
from kaiwen_agent.tasks.models import AgentTask, TaskStatus
from kaiwen_agent.types import AgentRun, utc_now

T = TypeVar("T")


class SQLitePersistence:
    """Dependency-free SQLite reference adapter for local and small deployments."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def initialize(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            await self._run(self._create_schema)
            self._initialized = True

    async def save_session(self, session: SessionRecord) -> None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO sessions (id, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at""",
                (
                    session.id,
                    json.dumps(session.metadata, ensure_ascii=False, default=str),
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                ),
            )

        await self._run(operation)

    async def get_session(self, session_id: str) -> SessionRecord | None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> SessionRecord | None:
            row = connection.execute(
                "SELECT id, metadata_json, created_at, updated_at FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            return SessionRecord(
                id=row["id"],
                metadata=json.loads(row["metadata_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

        return await self._run(operation)

    async def save(self, run: AgentRun) -> None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO runs (id, session_id, status, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    completed_at = excluded.completed_at""",
                (
                    run.id,
                    run.session_id,
                    run.status,
                    run.created_at.isoformat(),
                    run.completed_at.isoformat() if run.completed_at else None,
                ),
            )

        await self._run(operation)

    async def get(self, run_id: str) -> AgentRun | None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> AgentRun | None:
            row = connection.execute(
                "SELECT id, session_id, status, created_at, completed_at FROM runs WHERE id = ?",
                (run_id,),
            ).fetchone()
            if row is None:
                return None
            return AgentRun(
                id=row["id"],
                session_id=row["session_id"],
                status=row["status"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )

        return await self._run(operation)

    async def append(self, event: AgentEvent) -> None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO events
                    (id, type, timestamp, trace_id, session_id, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    event.id,
                    event.type,
                    event.timestamp.isoformat(),
                    event.trace_id,
                    event.session_id,
                    json.dumps(event.payload, ensure_ascii=False, default=str),
                ),
            )

        await self._run(operation)

    async def list_events(
        self,
        *,
        session_id: str,
        after_id: str | None = None,
        limit: int = 100,
    ) -> list[AgentEvent]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> list[AgentEvent]:
            after_sequence = 0
            if after_id is not None:
                cursor = connection.execute(
                    "SELECT sequence FROM events WHERE id = ? AND session_id = ?",
                    (after_id, session_id),
                ).fetchone()
                if cursor is None:
                    return []
                after_sequence = int(cursor["sequence"])
            rows = connection.execute(
                """SELECT id, type, timestamp, trace_id, session_id, payload_json
                FROM events WHERE session_id = ? AND sequence > ?
                ORDER BY sequence ASC LIMIT ?""",
                (session_id, after_sequence, limit),
            ).fetchall()
            return [
                AgentEvent(
                    id=row["id"],
                    type=row["type"],
                    timestamp=row["timestamp"],
                    trace_id=row["trace_id"],
                    session_id=row["session_id"],
                    payload=json.loads(row["payload_json"]),
                )
                for row in rows
            ]

        return await self._run(operation)

    async def append_audit(self, record: AuditRecord) -> None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO audit_log
                    (id, trace_id, session_id, action, outcome, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.id,
                    record.trace_id,
                    record.session_id,
                    record.action,
                    record.outcome,
                    json.dumps(record.details, ensure_ascii=False, default=str),
                    record.timestamp.isoformat(),
                ),
            )

        await self._run(operation)

    async def save_task(self, task: AgentTask) -> None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO tasks
                    (id, status, agent_id, parent_id, task_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    agent_id = excluded.agent_id,
                    parent_id = excluded.parent_id,
                    task_json = excluded.task_json,
                    updated_at = excluded.updated_at""",
                (
                    task.id,
                    task.status,
                    task.agent_id,
                    task.parent_id,
                    task.model_dump_json(),
                    utc_now().isoformat(),
                ),
            )

        await self._run(operation)

    async def get_task(self, task_id: str) -> AgentTask | None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> AgentTask | None:
            row = connection.execute(
                "SELECT task_json FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            return AgentTask.model_validate_json(row["task_json"]) if row else None

        return await self._run(operation)

    async def append_message(self, message: ConversationMessage) -> None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT OR IGNORE INTO conversation_messages
                    (id, tenant_id, conversation_id, user_id, message_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    message.id,
                    message.tenant_id,
                    message.conversation_id,
                    message.user_id,
                    message.model_dump_json(),
                    message.created_at.isoformat(),
                ),
            )

        await self._run(operation)

    async def list_messages(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        after_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationMessage]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> list[ConversationMessage]:
            after_sequence = 0
            if after_id is not None:
                cursor = connection.execute(
                    """SELECT sequence FROM conversation_messages
                    WHERE id = ? AND tenant_id = ? AND conversation_id = ?""",
                    (after_id, tenant_id, conversation_id),
                ).fetchone()
                if cursor is None:
                    return []
                after_sequence = int(cursor["sequence"])
            rows = connection.execute(
                """SELECT message_json FROM conversation_messages
                WHERE tenant_id = ? AND conversation_id = ? AND sequence > ?
                ORDER BY sequence ASC LIMIT ?""",
                (tenant_id, conversation_id, after_sequence, limit),
            ).fetchall()
            return [
                ConversationMessage.model_validate_json(row["message_json"])
                for row in rows
            ]

        return await self._run(operation)

    async def list_tasks(self, *, status: TaskStatus | None = None) -> list[AgentTask]:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> list[AgentTask]:
            if status is None:
                rows = connection.execute(
                    "SELECT task_json FROM tasks ORDER BY rowid ASC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT task_json FROM tasks WHERE status = ? ORDER BY rowid ASC",
                    (status,),
                ).fetchall()
            return [AgentTask.model_validate_json(row["task_json"]) for row in rows]

        return await self._run(operation)

    async def save_checkpoint(self, checkpoint: TaskCheckpoint) -> None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> None:
            connection.execute(
                """INSERT INTO task_checkpoints
                    (id, task_id, sequence, checkpoint_json, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    checkpoint.id,
                    checkpoint.task_id,
                    checkpoint.sequence,
                    checkpoint.model_dump_json(),
                    checkpoint.created_at.isoformat(),
                ),
            )

        await self._run(operation)

    async def latest_checkpoint(self, task_id: str) -> TaskCheckpoint | None:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> TaskCheckpoint | None:
            row = connection.execute(
                """SELECT checkpoint_json FROM task_checkpoints
                WHERE task_id = ? ORDER BY sequence DESC LIMIT 1""",
                (task_id,),
            ).fetchone()
            return TaskCheckpoint.model_validate_json(row["checkpoint_json"]) if row else None

        return await self._run(operation)

    async def list_audit(self, *, trace_id: str | None = None) -> list[AuditRecord]:
        await self.initialize()

        def operation(connection: sqlite3.Connection) -> list[AuditRecord]:
            query = """SELECT id, trace_id, session_id, action, outcome,
                details_json, timestamp FROM audit_log"""
            parameters: tuple[str, ...] = ()
            if trace_id is not None:
                query += " WHERE trace_id = ?"
                parameters = (trace_id,)
            query += " ORDER BY sequence ASC"
            rows = connection.execute(query, parameters).fetchall()
            return [
                AuditRecord(
                    id=row["id"],
                    trace_id=row["trace_id"],
                    session_id=row["session_id"],
                    action=row["action"],
                    outcome=row["outcome"],
                    details=json.loads(row["details_json"]),
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

        return await self._run(operation)

    async def _run(self, operation: Callable[[sqlite3.Connection], T]) -> T:
        def execute() -> T:
            connection = sqlite3.connect(self.path, timeout=30)
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("PRAGMA foreign_keys = ON")
                result = operation(connection)
                connection.commit()
                return result
            finally:
                connection.close()

        return await asyncio.to_thread(execute)

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            PRAGMA journal_mode = WAL;
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, completed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id);
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE, type TEXT NOT NULL, timestamp TEXT NOT NULL,
                trace_id TEXT NOT NULL, session_id TEXT NOT NULL, payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_session_sequence
                ON events(session_id, sequence);
            CREATE INDEX IF NOT EXISTS idx_events_trace ON events(trace_id);
            CREATE TABLE IF NOT EXISTS audit_log (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE, trace_id TEXT NOT NULL, session_id TEXT NOT NULL,
                action TEXT NOT NULL, outcome TEXT NOT NULL,
                details_json TEXT NOT NULL, timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audit_trace_sequence
                ON audit_log(trace_id, sequence);
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, status TEXT NOT NULL, agent_id TEXT NOT NULL,
                parent_id TEXT, task_json TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id);
            CREATE TABLE IF NOT EXISTS conversation_messages (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE, tenant_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL, user_id TEXT NOT NULL,
                message_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_scope_sequence
                ON conversation_messages(tenant_id, conversation_id, sequence);
            CREATE TABLE IF NOT EXISTS task_checkpoints (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                checkpoint_json TEXT NOT NULL, created_at TEXT NOT NULL,
                UNIQUE(task_id, sequence)
            );
            CREATE INDEX IF NOT EXISTS idx_checkpoints_task_sequence
                ON task_checkpoints(task_id, sequence);
            """
        )
