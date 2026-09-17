import assert from "node:assert/strict";
import test from "node:test";

import type { AgentEvent } from "@kaiwen/agent-protocol";

import { HttpSseTransport } from "../src/index.js";

class FakeEventSource {
  listeners = new Map<string, (event: { data: string }) => void>();
  closed = false;

  addEventListener(type: string, listener: (event: { data: string }) => void) {
    this.listeners.set(type, listener);
  }

  close() {
    this.closed = true;
  }

  emit(type: string, data: unknown) {
    this.listeners.get(type)?.({ data: JSON.stringify(data) });
  }
}

test("HTTP/SSE transport encodes commands and consumes named events", async () => {
  const requests: Array<{ url: string; body: unknown }> = [];
  const source = new FakeEventSource();
  let eventUrl = "";
  const fetcher = (async (input: RequestInfo | URL, init?: RequestInit) => {
    requests.push({
      url: String(input),
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
    });
    return new Response(null, { status: 204 });
  }) as typeof fetch;
  const transport = new HttpSseTransport({
    baseUrl: "https://agent.example.test/v1",
    fetch: fetcher,
    eventSourceFactory: (url) => {
      eventUrl = url;
      return source;
    },
  });
  const events: AgentEvent[] = [];
  const dispose = await transport.connect("session with space", (agentEvent) => {
    events.push(agentEvent);
  });

  assert.equal(
    eventUrl,
    "https://agent.example.test/v1/events?session_id=session%20with%20space",
  );
  source.emit("run.started", {
    schema_version: "1.0",
    id: "evt_1",
    type: "run.started",
    timestamp: "2026-09-17T12:00:00.000Z",
    trace_id: "trace-1",
    session_id: "session with space",
    payload: {},
  });
  source.listeners.get("message")?.({ data: "not-json" });
  source.emit("message", {
    schema_version: "1.0",
    id: "evt_unknown",
    type: "unknown.event",
    timestamp: "2026-09-17T12:00:00.000Z",
    trace_id: "trace-1",
    session_id: "session with space",
    payload: {},
  });
  assert.equal(events[0]?.type, "run.started");
  assert.equal(events.length, 1);

  await transport.sendInput("session-1", "Hello");
  await transport.sendCapabilities("session-1", {
    actions: [{ name: "navigate", schema: { type: "object" } }],
    artifacts: ["link"],
  });
  await transport.sendActionResult("session-1", "trace-1", {
    action_id: "action-1",
    name: "navigate",
    ok: true,
  });

  assert.deepEqual(requests.map(({ url }) => url), [
    "https://agent.example.test/v1/input",
    "https://agent.example.test/v1/capabilities",
    "https://agent.example.test/v1/actions/result",
  ]);
  assert.deepEqual(requests[1]?.body, {
    session_id: "session-1",
    actions: [{ name: "navigate", schema: { type: "object" } }],
    artifacts: ["link"],
  });

  dispose();
  assert.equal(source.closed, true);
});
