import type { AgentEvent, ArtifactType, ClientAction } from "@kaiwen/agent-protocol";

import { ActionRegistry } from "../actions/registry.js";
import type { AgentTransport, Dispose } from "../transports/types.js";
import {
  initialAgentUIState,
  reduceAgentEvent,
  type AgentUIState,
  type IslandMode,
} from "./state.js";

export type StateListener = (state: AgentUIState) => void;

export class AgentUIRuntime {
  private state: AgentUIState = initialAgentUIState;
  private readonly listeners = new Set<StateListener>();
  private readonly seenEvents = new Set<string>();
  private disposeTransport?: Dispose;

  constructor(
    private readonly transport: AgentTransport,
    private readonly actions: ActionRegistry = new ActionRegistry(),
    private readonly artifactTypes: ArtifactType[] = [],
  ) {}

  getState(): AgentUIState {
    return this.state;
  }

  subscribe(listener: StateListener): Dispose {
    this.listeners.add(listener);
    listener(this.getState());
    return () => this.listeners.delete(listener);
  }

  async connect(sessionId: string): Promise<void> {
    this.disconnect();
    this.patch({ sessionId, connection: "connecting" });
    try {
      this.disposeTransport = await this.transport.connect(sessionId, (event) =>
        this.handleEvent(event),
      );
      await this.transport.sendCapabilities(sessionId, {
        actions: this.actions.capabilities(),
        artifacts: [...this.artifactTypes],
      });
      this.patch({ connection: "connected", error: undefined });
    } catch (error) {
      this.disposeTransport?.();
      this.disposeTransport = undefined;
      this.patch({
        connection: "disconnected",
        error: error instanceof Error ? error.message : "Agent connection failed",
      });
      throw error;
    }
  }

  disconnect(): void {
    this.disposeTransport?.();
    this.disposeTransport = undefined;
    this.seenEvents.clear();
    this.patch({ sessionId: null, connection: "disconnected" });
  }

  async submit(text: string): Promise<void> {
    const value = text.trim();
    if (!value) throw new Error("Agent input cannot be empty");
    if (!this.state.sessionId || this.state.connection !== "connected") {
      throw new Error("Agent UI runtime is not connected");
    }
    this.patch({ mode: "thinking", text: "", artifacts: [], error: undefined });
    try {
      await this.transport.sendInput(this.state.sessionId, value);
    } catch (error) {
      this.patch({
        mode: "result",
        error: error instanceof Error ? error.message : "Agent input failed",
      });
      throw error;
    }
  }

  setMode(mode: IslandMode): void {
    this.patch({ mode });
  }

  compact(): void {
    this.patch({ mode: "compact" });
  }

  reset(): void {
    this.patch({ mode: "idle", text: "", artifacts: [], error: undefined });
  }

  async handleEvent(event: AgentEvent): Promise<void> {
    if (this.seenEvents.has(event.id)) return;
    this.seenEvents.add(event.id);
    this.state = reduceAgentEvent(this.state, event);
    this.notify();

    if (event.type === "client_action.requested") {
      await this.executeClientAction(event);
    }
  }

  private async executeClientAction(event: AgentEvent): Promise<void> {
    const action = event.payload.action;
    if (!isClientAction(action) || !this.state.sessionId) return;
    this.patch({ mode: "tool_activity" });
    const result = await this.actions.execute(action, {
      sessionId: this.state.sessionId,
      traceId: event.trace_id,
    });
    await this.transport.sendActionResult(
      this.state.sessionId,
      event.trace_id,
      result,
    );
    this.patch({ mode: result.ok ? "thinking" : "result", error: result.error?.message });
  }

  private patch(patch: Partial<AgentUIState>): void {
    this.state = { ...this.state, ...patch };
    this.notify();
  }

  private notify(): void {
    const snapshot = this.getState();
    for (const listener of this.listeners) listener(snapshot);
  }
}

function isClientAction(value: unknown): value is ClientAction<Record<string, unknown>> {
  if (typeof value !== "object" || value === null) return false;
  const action = value as Partial<ClientAction<Record<string, unknown>>>;
  return (
    typeof action.id === "string" &&
    typeof action.name === "string" &&
    typeof action.arguments === "object" &&
    action.arguments !== null
  );
}
