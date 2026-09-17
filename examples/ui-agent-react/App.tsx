import { useMemo } from "react";

import {
  ActionRegistry,
  AgentUIRuntime,
  HttpSseTransport,
} from "@imthekaiwen/agent-ui";
import {
  AgentUIProvider,
  DynamicIsland,
  ReactArtifactRegistry,
} from "@imthekaiwen/agent-ui/react";

const artifacts = new ReactArtifactRegistry().register("project_card", ({ artifact }) => (
  <article>
    <small>Ürün</small>
    <strong>{String(artifact.data.title ?? "Kaiwen product")}</strong>
  </article>
));

export function App() {
  const runtime = useMemo(() => {
    const actions = new ActionRegistry()
      .register<{ path: string }, void>({
        name: "navigate",
        description: "Navigate inside the portfolio",
        schema: {
          type: "object",
          additionalProperties: false,
          required: ["path"],
          properties: { path: { type: "string", pattern: "^/" } },
        },
        handler: ({ path }) => {
          window.history.pushState({}, "", path);
          window.dispatchEvent(new PopStateEvent("popstate"));
        },
      })
      .register<{ productId: string }, void>({
        name: "open_product",
        description: "Open a product detail surface",
        schema: {
          type: "object",
          additionalProperties: false,
          required: ["productId"],
          properties: { productId: { type: "string", minLength: 1 } },
        },
        handler: ({ productId }) => {
          window.dispatchEvent(new CustomEvent("kaiwen:open-product", { detail: productId }));
        },
      });

    return new AgentUIRuntime(
      new HttpSseTransport({ baseUrl: "/api/agent" }),
      actions,
      ["project_card", "task_progress", "link"],
    );
  }, []);

  return (
    <AgentUIProvider runtime={runtime} sessionId="portfolio-session">
      <DynamicIsland
        labels={{
          idle: "Kai'ye sor",
          composing: "Mesajınızı yazın",
          thinking: "Düşünüyor",
          tool_activity: "Hazırlıyor",
          waiting_approval: "Onayınız gerekiyor",
        }}
        renderArtifact={(artifact) => artifacts.render(artifact)}
      />
    </AgentUIProvider>
  );
}
