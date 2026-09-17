export const SCHEMA_VERSION = "1.0" as const;

export const AGENT_EVENT_TYPES = [
  "conversation.input",
  "conversation.delta",
  "conversation.completed",
  "run.started",
  "run.status",
  "run.completed",
  "run.failed",
  "tool.started",
  "tool.completed",
  "tool.failed",
  "task.created",
  "task.queued",
  "task.started",
  "task.progress",
  "task.retrying",
  "task.paused",
  "task.resumed",
  "task.completed",
  "task.failed",
  "task.cancelled",
  "resource.waiting",
  "resource.acquired",
  "resource.released",
  "approval.requested",
  "approval.resolved",
  "artifact.created",
  "client.connected",
  "client.capabilities",
  "client.state",
  "client_action.requested",
  "client_action.result",
  "client_action.failed",
] as const;

export type AgentEventType =
  | "conversation.input"
  | "conversation.delta"
  | "conversation.completed"
  | "run.started"
  | "run.status"
  | "run.completed"
  | "run.failed"
  | "tool.started"
  | "tool.completed"
  | "tool.failed"
  | "task.created"
  | "task.queued"
  | "task.started"
  | "task.progress"
  | "task.retrying"
  | "task.paused"
  | "task.resumed"
  | "task.completed"
  | "task.failed"
  | "task.cancelled"
  | "resource.waiting"
  | "resource.acquired"
  | "resource.released"
  | "approval.requested"
  | "approval.resolved"
  | "artifact.created"
  | "client.connected"
  | "client.capabilities"
  | "client.state"
  | "client_action.requested"
  | "client_action.result"
  | "client_action.failed";

export interface AgentEvent<TPayload extends Record<string, unknown> = Record<string, unknown>> {
  schema_version: typeof SCHEMA_VERSION;
  id: `evt_${string}`;
  type: AgentEventType;
  timestamp: string;
  trace_id: string;
  session_id: string;
  payload: TPayload;
}

export type ArtifactType =
  | "project_card"
  | "task_progress"
  | "approval_card"
  | "form_draft"
  | "notification"
  | "link";

export interface AgentArtifact<TData extends Record<string, unknown> = Record<string, unknown>> {
  id: string;
  type: ArtifactType;
  data: TData;
}

export interface ClientAction<TArguments extends Record<string, unknown> = Record<string, unknown>> {
  id: string;
  name: string;
  arguments: TArguments;
  timeout_ms?: number;
}
