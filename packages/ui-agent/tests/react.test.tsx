import assert from "node:assert/strict";
import test from "node:test";

import { renderToStaticMarkup } from "react-dom/server";

import { AgentUIRuntime, type AgentTransport, type ClientCapabilities } from "../src/index.js";
import {
  AgentUIProvider,
  DynamicIsland,
  ReactArtifactRegistry,
} from "../src/react/index.js";

const transport: AgentTransport = {
  async connect() {
    return () => undefined;
  },
  async sendInput() {},
  async sendActionResult() {},
  async sendCapabilities(_sessionId: string, _capabilities: ClientCapabilities) {},
};

test("React bindings render a themeable, accessible Dynamic Island", () => {
  const runtime = new AgentUIRuntime(transport);
  const html = renderToStaticMarkup(
    <AgentUIProvider autoConnect={false} runtime={runtime} sessionId="session-1">
      <DynamicIsland labels={{ idle: "Kai ile konuş" }} />
    </AgentUIProvider>,
  );

  assert.match(html, /data-agent-island/);
  assert.match(html, /Kai ile konuş/);
  assert.match(html, /aria-label="Agent message"/);
});

test("React artifact registry renders only registered artifact types", () => {
  const registry = new ReactArtifactRegistry().register("project_card", ({ artifact }) => (
    <article>{String(artifact.data.title)}</article>
  ));
  const rendered = registry.render({
    id: "project-1",
    type: "project_card",
    data: { title: "Cube Rivals" },
  });

  assert.equal(renderToStaticMarkup(<>{rendered}</>), "<article>Cube Rivals</article>");
  assert.equal(registry.render({ id: "link-1", type: "link", data: {} }), null);
});
