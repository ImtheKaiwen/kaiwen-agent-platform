import type { AgentArtifact, ArtifactType } from "@kaiwen/agent-protocol";
import type { ComponentType, ReactNode } from "react";

export type ReactArtifactRenderer = ComponentType<{ artifact: AgentArtifact }>;

export class ReactArtifactRegistry {
  private readonly renderers = new Map<ArtifactType, ReactArtifactRenderer>();

  register(type: ArtifactType, renderer: ReactArtifactRenderer): this {
    if (this.renderers.has(type)) throw new Error(`Artifact renderer already registered: ${type}`);
    this.renderers.set(type, renderer);
    return this;
  }

  render(artifact: AgentArtifact): ReactNode {
    const Renderer = this.renderers.get(artifact.type);
    return Renderer ? <Renderer key={artifact.id} artifact={artifact} /> : null;
  }
}
