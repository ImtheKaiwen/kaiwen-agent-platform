import type { AgentEvent, ArtifactType } from "@imthekaiwen/agent-protocol";

import type { ActionCapability, ClientActionResult } from "../actions/types.js";

export type EventHandler = (event: AgentEvent) => void | Promise<void>;
export type Dispose = () => void;

export interface ClientCapabilities {
  actions: ActionCapability[];
  artifacts: ArtifactType[];
}

export interface AgentTransport {
  connect(sessionId: string, handler: EventHandler): Promise<Dispose>;
  sendInput(sessionId: string, text: string): Promise<void>;
  sendActionResult(
    sessionId: string,
    traceId: string,
    result: ClientActionResult,
  ): Promise<void>;
  sendCapabilities(sessionId: string, capabilities: ClientCapabilities): Promise<void>;
}
