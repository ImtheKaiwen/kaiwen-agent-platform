import type { AgentArtifact, ArtifactType } from "@imthekaiwen/agent-protocol";

export type ArtifactRenderer<TResult> = (artifact: AgentArtifact) => TResult;

export class ArtifactRegistry<TResult> {
  private readonly renderers = new Map<ArtifactType, ArtifactRenderer<TResult>>();

  register(type: ArtifactType, renderer: ArtifactRenderer<TResult>): this {
    if (this.renderers.has(type)) throw new Error(`Artifact renderer already registered: ${type}`);
    this.renderers.set(type, renderer);
    return this;
  }

  render(artifact: AgentArtifact): TResult | undefined {
    return this.renderers.get(artifact.type)?.(artifact);
  }

  capabilities(): ArtifactType[] {
    return [...this.renderers.keys()];
  }
}
