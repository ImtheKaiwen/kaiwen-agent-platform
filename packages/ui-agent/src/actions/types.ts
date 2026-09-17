import type { ClientAction } from "@imthekaiwen/agent-protocol";

export interface ActionContext {
  signal: AbortSignal;
  sessionId: string;
  traceId?: string;
}

export type ActionHandler<TArguments extends Record<string, unknown>, TResult> = (
  arguments_: TArguments,
  context: ActionContext,
) => TResult | Promise<TResult>;

export interface ActionCapability {
  name: string;
  schema: object;
  description?: string;
}

export interface ClientActionResult<TResult = unknown> {
  action_id: string;
  name: string;
  ok: boolean;
  data?: TResult;
  error?: {
    code: "unknown_action" | "invalid_arguments" | "timeout" | "execution_failed";
    message: string;
    details?: unknown;
  };
}

export interface ActionDefinition<
  TArguments extends Record<string, unknown> = Record<string, unknown>,
  TResult = unknown,
> {
  name: string;
  schema: object;
  handler: ActionHandler<TArguments, TResult>;
  description?: string;
}

export type SemanticClientAction = ClientAction<Record<string, unknown>>;
