"""ActionBenchmark model for 12-dimension scoring system."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ActionBenchmark:
    """Represents a scored action across 12 benchmark dimensions."""

    action_id: str
    actor_id: str
    timestamp: str
    action_type: str

    # 12 benchmark dimensions (all float 0-100)
    time_leverage: float = 50.0
    effort_intensity: float = 50.0
    output_quality: float = 50.0
    uniqueness: float = 50.0
    relational_capital: float = 50.0
    risk_reduction: float = 50.0
    probability_lift: float = 50.0
    multiplicative_effect: float = 50.0
    brand_adherence: float = 50.0
    interaction_effectiveness: float = 50.0
    economic_productivity: float = 50.0
    ethos_alignment: float = 50.0

    confidence: float = 0.5  # 0-1
    attribution_links: List[str] = field(default_factory=list)
    notes: str = ""

    def get_all_dimensions(self) -> dict:
        """Return all 12 benchmark dimensions as a dictionary."""
        return {
            "time_leverage": self.time_leverage,
            "effort_intensity": self.effort_intensity,
            "output_quality": self.output_quality,
            "uniqueness": self.uniqueness,
            "relational_capital": self.relational_capital,
            "risk_reduction": self.risk_reduction,
            "probability_lift": self.probability_lift,
            "multiplicative_effect": self.multiplicative_effect,
            "brand_adherence": self.brand_adherence,
            "interaction_effectiveness": self.interaction_effectiveness,
            "economic_productivity": self.economic_productivity,
            "ethos_alignment": self.ethos_alignment,
        }
