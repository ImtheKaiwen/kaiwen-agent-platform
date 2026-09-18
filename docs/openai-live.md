# OpenAI Live adapter

The OpenAI adapter implements the current Live wire contract behind the
provider-neutral Realtime Core. Provider SDK types do not enter core models.

## Current support boundary

`0.3.0a1` supports a primary server WebSocket, server-authorized browser WebRTC
bootstrap, and trusted backend sideband attachment to an existing Live session. The
sideband uses the official `/v1/live/sessions/{session_id}/attach` contract. It never
sends `session.start` or primary audio, and closing it does not close the browser or
SIP media connection.

Responses-delegation function calls can be executed through the runtime's existing
`ToolExecutor`. Permissions, approval, idempotency, retry, and audit remain
application-composed server concerns; the browser receives neither credentials nor
tool authority.

## Install

```bash
pip install "kaiwen-agent[openai-live]"
```

The extra installs the optional WebSocket transport. The WebRTC bootstrap uses the
Python standard library and can be replaced with an application-owned HTTP transport.

## Primary backend WebSocket

```python
from kaiwen_agent.realtime import (
    OpenAILiveProvider,
    OpenAILiveProviderOptions,
    RealtimeSessionConfig,
    RealtimeSessionManager,
)

provider = OpenAILiveProvider(
    api_key=settings.openai_api_key,
    options=OpenAILiveProviderOptions(
        instructions="Keep spoken replies concise.",
        voice="marin",
        response_model="gpt-5-mini",
    ),
)
manager = RealtimeSessionManager([provider])
session = await manager.create_session(
    RealtimeSessionConfig(provider="openai-live", model="gpt-live-1"),
    conversation_id="conversation_123",
    tenant_id="tenant_123",
    user_id="user_123",
)
```

The adapter opens `wss://api.openai.com/v1/live`, sends `session.start`, and does not
return a connection until `session.started` supplies the provider session ID. Audio
sent over this primary WebSocket is raw mono PCM16LE at 24 kHz and is base64 encoded
without a container header.

Text input uses `response.item.create` followed by `response.create`, so it requires
`response_model` and Responses delegation. Product text chat should still converge in
the R3 conversation bridge rather than treating the Live provider timeline as durable
history.

Live handles barge-in when new input audio arrives. `interrupt()` makes sure input is
unmuted; generated audio playback cancellation on WebRTC remains a client transport
responsibility.

## Browser WebRTC bootstrap

```python
from kaiwen_agent.realtime import OpenAILiveProviderOptions, OpenAILiveWebRTCService

service = OpenAILiveWebRTCService(api_key=settings.openai_api_key)
answer = await service.create_session(
    sdp_offer=browser_offer,
    config=RealtimeSessionConfig(provider="openai-live", model="gpt-live-1"),
    options=OpenAILiveProviderOptions(
        response_model="gpt-5.6-luna",
        response_instructions="Use verified application records.",
    ),
    tools=admin_tools,
)
```

Expose only `answer.session_id` and `answer.sdp_answer` to the authenticated browser.
Never return the server API key. The browser applies the SDP answer and waits for
`session.started` on its data channel before sending commands.

## Trusted sideband tool execution

Attach only after loading the logical realtime session through trusted application
identity and ownership checks:

```python
from kaiwen_agent import AgentContext, ToolExecutor
from kaiwen_agent.realtime import (
    OpenAILiveSidebandService,
    OpenAILiveSidebandToolBridge,
)

connection = await OpenAILiveSidebandService(
    api_key=settings.openai_api_key,
).attach(realtime_session)

bridge = OpenAILiveSidebandToolBridge(
    connection,
    tools=admin_tools,
    tool_executor=ToolExecutor(
        approval_gate=approval_gate,
        idempotency_store=idempotency_store,
        audit_store=audit_store,
    ),
    context=AgentContext(
        session_id=realtime_session.id,
        tenant_id=realtime_session.tenant_id,
        user_id=realtime_session.user_id,
        permissions=admin_permissions,
        services=application_services,
    ),
)
await bridge.run()
```

The bridge waits for completed nested `response.output_item.done` calls, submits all
results before one `response.create`, ignores duplicate completed response events,
and returns sanitized error codes to the delegated model. A tool marked
`requires_approval=True` cannot run without an application-owned approval gate.

The connection verifies that the tool context matches the logical realtime session,
tenant, and user used during attachment. Provider session IDs remain transport
metadata and never become authorization identities.

## Normalized events

The adapter currently maps:

- input/output transcript fragments to `realtime.transcript.delta`;
- output audio chunks to `realtime.audio.output`;
- cumulative usage to `realtime.usage.updated`;
- nested completed Responses events to `realtime.turn.completed`;
- terminal session and error events to durable provider events.

Unknown provider events are ignored deliberately so additive OpenAI event types do
not break the runtime. The R3 conversation bridge assembles transcript deltas into
durable conversation messages and exposes only stable semantic events.
