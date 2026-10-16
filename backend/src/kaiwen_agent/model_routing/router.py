from __future__ import annotations

from kaiwen_agent.model_routing.models import (
    ModelComplexity,
    ModelRoute,
    ModelSelection,
    ModelTier,
)
from kaiwen_agent.policy import PolicyContext, PolicyDecisionType, PolicyEngine


class ModelRouteUnavailableError(LookupError):
    pass


class ModelRouter:
    """Resolves model identifiers; it never creates provider clients."""

    def __init__(self, *, routes: list[ModelRoute], policy_engine: PolicyEngine) -> None:
        ids = [route.id for route in routes]
        if len(ids) != len(set(ids)):
            raise ValueError("Model route ids must be unique")
        self.routes = tuple(routes)
        self.policy_engine = policy_engine

    async def resolve(
        self,
        *,
        capability: str,
        complexity: ModelComplexity,
        policy_context: PolicyContext,
        allowed_tiers: frozenset[ModelTier] | None = None,
    ) -> ModelSelection:
        candidates = [
            route
            for route in self.routes
            if route.enabled
            and capability in route.capabilities
            and complexity in route.complexities
            and (allowed_tiers is None or route.tier in allowed_tiers)
        ]
        candidates.sort(key=lambda route: route.priority, reverse=True)
        for route in candidates:
            decision = await self.policy_engine.evaluate(
                policy_context.model_copy(
                    update={
                        "action": "model.resolve",
                        "resource": route.id,
                        "metadata": {
                            **policy_context.metadata,
                            "capability": capability,
                            "complexity": complexity.value,
                            "provider": route.provider,
                            "model": route.model,
                            "tier": route.tier.value,
                        },
                    }
                )
            )
            if decision.decision != PolicyDecisionType.ALLOW:
                continue
            return ModelSelection(
                route_id=route.id,
                provider=route.provider,
                model=route.model,
                tier=route.tier,
                capability=capability,
                complexity=complexity,
            )
        raise ModelRouteUnavailableError(
            f"No policy-allowed model route for {capability}/{complexity.value}"
        )
