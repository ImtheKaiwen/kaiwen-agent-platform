import {
  createContext,
  type PropsWithChildren,
  useContext,
  useEffect,
  useSyncExternalStore,
} from "react";

import type { AgentUIRuntime } from "../runtime/runtime.js";
import type { AgentUIState } from "../runtime/state.js";

const RuntimeContext = createContext<AgentUIRuntime | null>(null);

export interface AgentUIProviderProps extends PropsWithChildren {
  runtime: AgentUIRuntime;
  sessionId: string;
  autoConnect?: boolean;
  onConnectionError?: (error: unknown) => void;
}

export function AgentUIProvider({
  runtime,
  sessionId,
  autoConnect = true,
  onConnectionError,
  children,
}: AgentUIProviderProps) {
  useEffect(() => {
    if (!autoConnect) return;
    void runtime.connect(sessionId).catch(onConnectionError);
    return () => runtime.disconnect();
  }, [autoConnect, onConnectionError, runtime, sessionId]);

  return <RuntimeContext.Provider value={runtime}>{children}</RuntimeContext.Provider>;
}

export function useAgentRuntime(): AgentUIRuntime {
  const runtime = useContext(RuntimeContext);
  if (!runtime) throw new Error("useAgentRuntime must be used inside AgentUIProvider");
  return runtime;
}

export function useAgentUI(): AgentUIState {
  const runtime = useAgentRuntime();
  return useSyncExternalStore(
    (listener) => runtime.subscribe(listener),
    () => runtime.getState(),
    () => runtime.getState(),
  );
}
