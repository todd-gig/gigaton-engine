"""CompensationEvent model for compensation calculations."""

from dataclasses import dataclass


@dataclass
class CompensationEvent:
    """Represents a compensation event with breakdown of components."""

    comp_event_id: str
    actor_id: str
    period_id: str
    base_amount: float
    variable_amount: float
    total_amount: float
    multiplier: float = 1.0
    ethos_coefficient: float = 1.0
    penalties: float = 0.0
    deferred_accrual: float = 0.0
    explanation: str = ""
