import assert from "node:assert/strict";
import test from "node:test";

import { ActionRegistry } from "../src/index.js";

const context = { sessionId: "session-1", traceId: "trace-1" };

test("action registry validates arguments and executes an allowlisted action", async () => {
  const registry = new ActionRegistry().register<{ path: string }, string>({
    name: "navigate",
    description: "Navigate inside the host application",
    schema: {
      type: "object",
      additionalProperties: false,
      required: ["path"],
      properties: { path: { type: "string", minLength: 1 } },
    },
    handler: ({ path }) => path,
  });

  assert.deepEqual(registry.capabilities(), [
    {
      name: "navigate",
      description: "Navigate inside the host application",
      schema: {
        type: "object",
        additionalProperties: false,
        required: ["path"],
        properties: { path: { type: "string", minLength: 1 } },
      },
    },
  ]);

  const valid = await registry.execute(
    { id: "action-1", name: "navigate", arguments: { path: "/projects" } },
    context,
  );
  assert.deepEqual(valid, {
    action_id: "action-1",
    name: "navigate",
    ok: true,
    data: "/projects",
  });

  const invalid = await registry.execute(
    { id: "action-2", name: "navigate", arguments: {} },
    context,
  );
  assert.equal(invalid.ok, false);
  assert.equal(invalid.error?.code, "invalid_arguments");
});

test("action registry denies unknown actions and aborts timed-out actions", async () => {
  const registry = new ActionRegistry().register({
    name: "wait",
    schema: { type: "object", additionalProperties: false },
    handler: async (_arguments, { signal }) =>
      new Promise((resolve, reject) => {
        signal.addEventListener("abort", () => reject(new Error("aborted")));
        setTimeout(resolve, 100);
      }),
  });

  const unknown = await registry.execute(
    { id: "action-3", name: "delete_everything", arguments: {} },
    context,
  );
  assert.equal(unknown.error?.code, "unknown_action");

  const timedOut = await registry.execute(
    { id: "action-4", name: "wait", arguments: {}, timeout_ms: 5 },
    context,
  );
  assert.equal(timedOut.error?.code, "timeout");
});

test("action registry rejects duplicate and non-semantic names", () => {
  const definition = {
    name: "open_modal",
    schema: { type: "object" },
    handler: () => undefined,
  };
  const registry = new ActionRegistry().register(definition);
  assert.throws(() => registry.register(definition), /already registered/);
  assert.throws(
    () => registry.register({ ...definition, name: "Click Button" }),
    /Invalid semantic action name/,
  );
});
