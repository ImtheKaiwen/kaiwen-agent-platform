import asyncio
import json

from kaiwen_agent.events import AgentEvent, InMemoryEventSink
from kaiwen_agent.transports.sse import SSEEventBroker, encode_sse


def test_encode_sse_uses_id_type_and_json_payload() -> None:
    event = AgentEvent(
        id="evt_1",
        type="run.started",
        trace_id="trace_1",
        session_id="session_1",
        payload={"agent": "test"},
    )
    encoded = encode_sse(event)
    assert encoded.startswith("id: evt_1\nevent: run.started\ndata: ")
    data = json.loads(encoded.split("data: ", 1)[1])
    assert data["payload"] == {"agent": "test"}


def test_sse_broker_persists_and_fans_out_by_session() -> None:
    async def scenario() -> None:
        sink = InMemoryEventSink()
        broker = SSEEventBroker(sink)
        stream = broker.stream("session_1")
        next_event = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        await broker.append(
            AgentEvent(
                id="evt_1",
                type="run.started",
                trace_id="trace_1",
                session_id="session_1",
            )
        )
        encoded = await asyncio.wait_for(next_event, timeout=1)
        await stream.aclose()
        assert "event: run.started" in encoded
        assert [event.id for event in sink.events] == ["evt_1"]

    asyncio.run(scenario())
