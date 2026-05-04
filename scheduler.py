from __future__ import annotations

from dataclasses import dataclass

from .models import PriorityTier


@dataclass
class PriorityDecision:
    priority_id: int
    tier: PriorityTier


class PMLFQScheduler:
    def assign_priority(self, predicted_runtime_ms: float) -> PriorityDecision:
        if predicted_runtime_ms <= 100:
            return PriorityDecision(priority_id=0, tier=PriorityTier.EXPRESS)
        if predicted_runtime_ms <= 600:
            return PriorityDecision(priority_id=1, tier=PriorityTier.STANDARD)
        return PriorityDecision(priority_id=2, tier=PriorityTier.BATCH)

    def demote_if_needed(
        self,
        current_tier: PriorityTier,
        predicted_runtime_ms: float,
        observed_runtime_ms: float,
    ) -> PriorityDecision:
        # Demote if runtime drifts 35% above prediction.
        if observed_runtime_ms <= predicted_runtime_ms * 1.35:
            return PriorityDecision(
                priority_id=self._tier_to_id(current_tier),
                tier=current_tier,
            )
        if current_tier == PriorityTier.EXPRESS:
            return PriorityDecision(priority_id=1, tier=PriorityTier.STANDARD)
        if current_tier == PriorityTier.STANDARD:
            return PriorityDecision(priority_id=2, tier=PriorityTier.BATCH)
        return PriorityDecision(priority_id=2, tier=PriorityTier.BATCH)

    @staticmethod
    def _tier_to_id(tier: PriorityTier) -> int:
        return {
            PriorityTier.EXPRESS: 0,
            PriorityTier.STANDARD: 1,
            PriorityTier.BATCH: 2,
        }[tier]
