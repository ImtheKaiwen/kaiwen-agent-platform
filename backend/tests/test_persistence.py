import asyncio

from kaiwen_agent.audit import AuditRecord, RedactingAuditStore
from kaiwen_agent.control import RunControl, TaskCheckpoint
from kaiwen_agent.events import AgentEvent
from kaiwen_agent.persistence.sqlite import SQLitePersistence
from kaiwen_agent.realtime import ConversationMessage, ConversationModality, ConversationRole
from kaiwen_agent.sessions import SessionRecord
from kaiwen_agent.tasks import AgentTask, TaskStatus
from kaiwen_agent.types import AgentRun


def test_sqlite_state_survives_adapter_restart(tmp_path) -> None:
    database = tmp_path / "agent.sqlite3"

    async def write() -> tuple[str, str]:
        store = SQLitePersistence(database)
        session = SessionRecord(id="session_1", metadata={"locale": "tr"})
        run = AgentRun(session_id=session.id, status="completed")
        event = AgentEvent(
            id="evt_first",
            type="run.started",
            trace_id="trace_1",
            session_id=session.id,
            payload={"step": 1},
        )
        await store.save_session(session)
        await store.save(run)
        await store.append(event)
        return run.id, event.id

    run_id, event_id = asyncio.run(write())

    async def read() -> None:
        restarted = SQLitePersistence(database)
        session = await restarted.get_session("session_1")
        run = await restarted.get(run_id)
        events = await restarted.list_events(session_id="session_1")
        assert session is not None and session.metadata == {"locale": "tr"}
        assert run is not None and run.status == "completed"
        assert [event.id for event in events] == [event_id]

    asyncio.run(read())


def test_sqlite_events_keep_append_order_and_cursor(tmp_path) -> None:
    async def scenario() -> None:
        store = SQLitePersistence(tmp_path / "events.sqlite3")
        for index in range(3):
            await store.append(
                AgentEvent(
                    id=f"evt_{index}",
                    type="run.status",
                    trace_id="trace_1",
                    session_id="session_1",
                    payload={"index": index},
                )
            )
        events = await store.list_events(session_id="session_1", after_id="evt_0")
        assert [event.id for event in events] == ["evt_1", "evt_2"]

    asyncio.run(scenario())


def test_audit_store_redacts_secrets_before_persistence(tmp_path) -> None:
    async def scenario() -> None:
        persistence = SQLitePersistence(tmp_path / "audit.sqlite3")
        store = RedactingAuditStore(persistence)
        await store.append_audit(
            AuditRecord(
                trace_id="trace_1",
                session_id="session_1",
                action="tool.execute",
                outcome="succeeded",
                details={
                    "api_key": "never-store-this",
                    "nested": {"authorization": "Bearer secret-token-value"},
                    "message": "key sk-abcdefghijklmnopqrstuvwxyz used",
                },
            )
        )
        records = await persistence.list_audit(trace_id="trace_1")
        assert records[0].details["api_key"] == "[REDACTED]"
        assert records[0].details["nested"]["authorization"] == "[REDACTED]"
        assert "sk-" not in records[0].details["message"]

    asyncio.run(scenario())


def test_task_and_checkpoint_survive_adapter_restart(tmp_path) -> None:
    database = tmp_path / "tasks.sqlite3"

    async def write() -> None:
        store = SQLitePersistence(database)
        await store.save_task(
            AgentTask(
                id="task_1",
                name="Persist",
                agent_id="worker",
                status=TaskStatus.RUNNING,
                attempts=1,
            )
        )
        await store.save_checkpoint(
            TaskCheckpoint(task_id="task_1", sequence=1, state={"offset": 12})
        )

    asyncio.run(write())

    async def read() -> None:
        restarted = SQLitePersistence(database)
        task = await restarted.get_task("task_1")
        checkpoint = await restarted.latest_checkpoint("task_1")
        assert task is not None and task.status == TaskStatus.RUNNING
        assert checkpoint is not None and checkpoint.state == {"offset": 12}

    asyncio.run(read())


def test_run_control_continues_durable_checkpoint_sequence(tmp_path) -> None:
    database = tmp_path / "control.sqlite3"

    async def scenario() -> None:
        first_store = SQLitePersistence(database)
        await RunControl(checkpoints=first_store).checkpoint(
            "task_1", state={"step": 1}
        )
        restarted_store = SQLitePersistence(database)
        await RunControl(checkpoints=restarted_store).checkpoint(
            "task_1", state={"step": 2}
        )
        latest = await restarted_store.latest_checkpoint("task_1")
        assert latest is not None
        assert latest.sequence == 2
        assert latest.state == {"step": 2}

    asyncio.run(scenario())


def test_conversation_messages_are_durable_and_tenant_scoped(tmp_path) -> None:
    database = tmp_path / "conversations.sqlite3"

    async def write() -> str:
        store = SQLitePersistence(database)
        message = ConversationMessage(
            conversation_id="conversation_1",
            tenant_id="tenant_1",
            user_id="user_1",
            role=ConversationRole.USER,
            modality=ConversationModality.AUDIO,
            text="Merhaba",
        )
        await store.append_message(message)
        return message.id

    message_id = asyncio.run(write())

    async def read() -> None:
        store = SQLitePersistence(database)
        messages = await store.list_messages(
            tenant_id="tenant_1", conversation_id="conversation_1"
        )
        assert [message.id for message in messages] == [message_id]
        assert await store.list_messages(
            tenant_id="tenant_2", conversation_id="conversation_1"
        ) == []

    asyncio.run(read())
