import { AGENT_EVENT_TYPES, type AgentEvent } from "@imthekaiwen/agent-protocol";

import type { ClientActionResult } from "../actions/types.js";
import type {
  AgentTransport,
  ClientCapabilities,
  Dispose,
  EventHandler,
} from "./types.js";

interface EventMessage {
  data: string;
}

interface EventSourceLike {
  close(): void;
  addEventListener(type: string, listener: (event: EventMessage) => void): void;
}

export interface HttpSseTransportOptions {
  baseUrl: string;
  fetch?: typeof globalThis.fetch;
  eventSourceFactory?: (url: string) => EventSourceLike;
  headers?: Record<string, string>;
}

export class HttpSseTransport implements AgentTransport {
  private readonly fetcher: typeof globalThis.fetch;
  private readonly eventSourceFactory: (url: string) => EventSourceLike;

  constructor(private readonly options: HttpSseTransportOptions) {
    this.fetcher = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.eventSourceFactory =
      options.eventSourceFactory ?? ((url) => new EventSource(url) as EventSourceLike);
  }

  async connect(sessionId: string, handler: EventHandler): Promise<Dispose> {
    const url = `${this.options.baseUrl}/events?session_id=${encodeURIComponent(sessionId)}`;
    const source = this.eventSourceFactory(url);
    const receive = (message: EventMessage) => {
      try {
        const parsed: unknown = JSON.parse(message.data);
        if (isAgentEvent(parsed)) void Promise.resolve(handler(parsed)).catch(() => undefined);
      } catch {
        // Ignore malformed frames. The server owns canonical contract validation.
      }
    };
    source.addEventListener("message", receive);
    for (const type of AGENT_EVENT_TYPES) source.addEventListener(type, receive);
    return () => source.close();
  }

  async sendInput(sessionId: string, text: string): Promise<void> {
    await this.post("/input", { session_id: sessionId, text });
  }

  async sendActionResult(
    sessionId: string,
    traceId: string,
    result: ClientActionResult,
  ): Promise<void> {
    await this.post("/actions/result", {
      session_id: sessionId,
      trace_id: traceId,
      result,
    });
  }

  async sendCapabilities(
    sessionId: string,
    capabilities: ClientCapabilities,
  ): Promise<void> {
    await this.post("/capabilities", { session_id: sessionId, ...capabilities });
  }

  private async post(path: string, body: unknown): Promise<void> {
    const response = await this.fetcher(`${this.options.baseUrl}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json", ...this.options.headers },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`Transport request failed: ${response.status}`);
  }
}

function isAgentEvent(value: unknown): value is AgentEvent {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<AgentEvent>;
  return (
    candidate.schema_version === "1.0" &&
    typeof candidate.id === "string" &&
    typeof candidate.type === "string" &&
    (AGENT_EVENT_TYPES as readonly string[]).includes(candidate.type) &&
    typeof candidate.trace_id === "string" &&
    typeof candidate.session_id === "string" &&
    typeof candidate.payload === "object" &&
    candidate.payload !== null
  );
}
