import type { AgentArtifact } from "@imthekaiwen/agent-protocol";
import { type CSSProperties, type FormEvent, type ReactNode, useState } from "react";

import type { IslandMode } from "../runtime/state.js";
import { useAgentRuntime, useAgentUI } from "./provider.js";

export interface DynamicIslandTheme {
  background?: string;
  color?: string;
  mutedColor?: string;
  accent?: string;
  border?: string;
  radius?: string;
  shadow?: string;
  width?: string;
}

export interface DynamicIslandProps {
  className?: string;
  placeholder?: string;
  ariaLabel?: string;
  theme?: DynamicIslandTheme;
  labels?: Partial<Record<IslandMode, string>>;
  renderArtifact?: (artifact: AgentArtifact) => ReactNode;
}

const defaultLabels: Record<IslandMode, string> = {
  idle: "Ask Kai",
  listening: "Listening",
  composing: "Write a message",
  thinking: "Thinking",
  tool_activity: "Working",
  waiting_approval: "Approval required",
  waiting_user: "Waiting for you",
  result: "Kai",
  compact: "Kai",
};

export function DynamicIsland({
  className,
  placeholder = "Write a message...",
  ariaLabel = "Kai agent",
  theme,
  labels,
  renderArtifact,
}: DynamicIslandProps) {
  const runtime = useAgentRuntime();
  const state = useAgentUI();
  const [input, setInput] = useState("");
  const [submitError, setSubmitError] = useState<string>();
  const resolvedLabels = { ...defaultLabels, ...labels };
  const compact = state.mode === "compact";
  const mutedColor = theme?.mutedColor ?? "rgba(255,255,255,.62)";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = input.trim();
    if (!value) return;
    setSubmitError(undefined);
    try {
      await runtime.submit(value);
      setInput("");
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Message could not be sent");
    }
  }

  const style: CSSProperties = {
    background: theme?.background ?? "#0f0f10",
    color: theme?.color ?? "#ffffff",
    border: theme?.border ?? "1px solid rgba(255,255,255,.12)",
    borderRadius: theme?.radius ?? "24px",
    boxShadow: theme?.shadow ?? "0 18px 48px rgba(0,0,0,.24)",
    boxSizing: "border-box",
    width: compact ? "auto" : (theme?.width ?? "min(420px, calc(100vw - 24px))"),
    maxWidth: "calc(100vw - 24px)",
    padding: compact ? "10px 16px" : "16px",
    transition: "width 220ms ease, border-radius 220ms ease, padding 220ms ease",
  };

  return (
    <section
      aria-label={ariaLabel}
      aria-live="polite"
      className={className}
      data-agent-island=""
      data-state={state.mode}
      style={style}
    >
      <header style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span
          aria-hidden="true"
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: theme?.accent ?? "#b7a3ff",
          }}
        />
        <strong style={{ flex: 1, fontSize: 13 }}>{resolvedLabels[state.mode]}</strong>
        <span style={{ color: mutedColor, fontSize: 11 }}>{state.connection}</span>
        <button
          aria-label={compact ? "Expand agent" : "Compact agent"}
          onClick={() => (compact ? runtime.reset() : runtime.compact())}
          style={iconButtonStyle}
          type="button"
        >
          {compact ? "+" : "−"}
        </button>
      </header>

      {!compact && (
        <div style={{ display: "grid", gap: 12, marginTop: 14 }}>
          {state.text && <div style={{ lineHeight: 1.5, fontSize: 14 }}>{state.text}</div>}
          {(state.error ?? submitError) && (
            <div role="alert" style={{ color: "#ffb4ab", fontSize: 13 }}>
              {state.error ?? submitError}
            </div>
          )}
          {state.progress !== undefined && (
            <progress aria-label="Task progress" max={1} value={state.progress} />
          )}
          {renderArtifact && state.artifacts.map((artifact) => renderArtifact(artifact))}
          <form onSubmit={submit} style={{ display: "flex", gap: 8 }}>
            <input
              aria-label="Agent message"
              disabled={state.connection !== "connected"}
              onChange={(event) => setInput(event.target.value)}
              onFocus={() => runtime.setMode("composing")}
              placeholder={placeholder}
              style={{
                flex: 1,
                minWidth: 0,
                border: "1px solid rgba(255,255,255,.14)",
                borderRadius: 999,
                background: "rgba(255,255,255,.08)",
                color: "inherit",
                padding: "10px 14px",
                outline: "none",
              }}
              value={input}
            />
            <button
              aria-label="Send message"
              disabled={!input.trim() || state.connection !== "connected"}
              style={{ ...iconButtonStyle, width: 40, height: 40 }}
              type="submit"
            >
              ↑
            </button>
          </form>
        </div>
      )}
    </section>
  );
}

const iconButtonStyle: CSSProperties = {
  border: 0,
  borderRadius: "50%",
  background: "rgba(255,255,255,.1)",
  color: "inherit",
  cursor: "pointer",
};
