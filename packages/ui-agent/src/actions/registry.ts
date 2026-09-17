import { Ajv, type ValidateFunction } from "ajv";

import type {
  ActionCapability,
  ActionContext,
  ActionDefinition,
  ClientActionResult,
  SemanticClientAction,
} from "./types.js";

interface CompiledAction {
  definition: ActionDefinition;
  validate: ValidateFunction;
}

export class ActionRegistry {
  private readonly actions = new Map<string, CompiledAction>();
  private readonly ajv: Ajv;

  constructor(ajv = new Ajv({ allErrors: true, strict: true })) {
    this.ajv = ajv;
  }

  register<TArguments extends Record<string, unknown>, TResult>(
    definition: ActionDefinition<TArguments, TResult>,
  ): this {
    if (!/^[a-z][a-z0-9_.-]*$/.test(definition.name)) {
      throw new Error(`Invalid semantic action name: ${definition.name}`);
    }
    if (this.actions.has(definition.name)) {
      throw new Error(`Action already registered: ${definition.name}`);
    }
    this.actions.set(definition.name, {
      definition: definition as ActionDefinition,
      validate: this.ajv.compile(definition.schema),
    });
    return this;
  }

  capabilities(): ActionCapability[] {
    return [...this.actions.values()].map(({ definition }) => ({
      name: definition.name,
      schema: definition.schema,
      ...(definition.description ? { description: definition.description } : {}),
    }));
  }

  async execute(
    action: SemanticClientAction,
    context: Omit<ActionContext, "signal">,
  ): Promise<ClientActionResult> {
    const compiled = this.actions.get(action.name);
    if (!compiled) {
      return this.failure(action, "unknown_action", `Unknown action: ${action.name}`);
    }
    if (!compiled.validate(action.arguments)) {
      return this.failure(
        action,
        "invalid_arguments",
        `Invalid arguments for ${action.name}`,
        compiled.validate.errors,
      );
    }

    const controller = new AbortController();
    const timeoutMs = action.timeout_ms ?? 10_000;
    let timeout: ReturnType<typeof setTimeout> | undefined;
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        timeout = setTimeout(() => {
          controller.abort();
          reject(new ActionTimeoutError());
        }, timeoutMs);
      });
      const data = await Promise.race([
        compiled.definition.handler(action.arguments, {
          ...context,
          signal: controller.signal,
        }),
        timeoutPromise,
      ]);
      return { action_id: action.id, name: action.name, ok: true, data };
    } catch (error) {
      if (error instanceof ActionTimeoutError) {
        return this.failure(action, "timeout", `Action timed out after ${timeoutMs}ms`);
      }
      return this.failure(
        action,
        "execution_failed",
        error instanceof Error ? error.message : "Action execution failed",
      );
    } finally {
      if (timeout !== undefined) clearTimeout(timeout);
    }
  }

  private failure(
    action: SemanticClientAction,
    code: NonNullable<ClientActionResult["error"]>["code"],
    message: string,
    details?: unknown,
  ): ClientActionResult {
    return {
      action_id: action.id,
      name: action.name,
      ok: false,
      error: { code, message, ...(details === undefined ? {} : { details }) },
    };
  }
}

class ActionTimeoutError extends Error {}

export function createActionRegistry(): ActionRegistry {
  return new ActionRegistry();
}
