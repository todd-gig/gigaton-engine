"""Compensation engine implementing the compensation formula."""

import uuid

from l4_execution.engines.nocs_engine import NOCSResult
from l4_execution.models.compensation import CompensationEvent


class CompensationEngine:
    """Calculates compensation using the formula: C_i = B_i + (NSO_i * R * M_i * E_i) - P_i"""

    def __init__(self, payout_conversion_rate: float = 50.0):
        """
        Initialize compensation engine.

        Args:
            payout_conversion_rate: Dollar amount per NOCS point (default 50.0)
        """
        self.payout_conversion_rate = payout_conversion_rate

    def calculate(
        self,
        base_amount: float,
        nocs_result: NOCSResult,
        strategic_multiplier: float = 1.0,
        ethos_alignment_score: float = 50.0,
        penalties: float = 0.0,
        actor_id: str = "",
        period_id: str = "",
    ) -> CompensationEvent:
        """
        Calculate compensation using the formula.

        Formula: C_i = B_i + (NSO_i * R * M_i * E_i) - P_i

        Where:
            B_i = base_amount
            NSO_i = final_nocs (normalized to 0-1 scale)
            R = payout_conversion_rate
            M_i = strategic_multiplier (1.0-2.0)
            E_i = ethos_coefficient (derived from ethos_alignment_score)
            P_i = penalties

        Ethos coefficient rules:
            ethos_alignment >= 90: coefficient = 1.25
            ethos_alignment >= 70: coefficient = 1.0
            ethos_alignment >= 50: coefficient = 0.75
            ethos_alignment < 50: coefficient = 0.0 (disqualifying)

        Args:
            base_amount: Base compensation amount
            nocs_result: NOCSResult from NOCS engine
            strategic_multiplier: Multiplier for strategy importance (1.0-2.0)
            ethos_alignment_score: Ethos alignment score (0-100)
            penalties: Sum of penalty amounts to subtract
            actor_id: ID of the actor receiving compensation
            period_id: ID of the compensation period

        Returns:
            CompensationEvent with calculated amounts
        """
        # Calculate ethos coefficient
        ethos_coefficient = self._calculate_ethos_coefficient(ethos_alignment_score)

        # If disqualified (ethos < 50), variable component is zeroed out
        if ethos_alignment_score < 50:
            variable_amount = 0.0
            explanation = f"Disqualified: ethos_alignment_score={ethos_alignment_score} < 50"
        else:
            # Normalize NOCS to 0-1 scale (NOCS is 0-100)
            nocs_normalized = nocs_result.final_nocs / 100.0

            # Calculate variable component: NSO_i * R * M_i * E_i
            variable_amount = nocs_normalized * self.payout_conversion_rate * strategic_multiplier * ethos_coefficient

            explanation = (
                f"Base: {base_amount:.2f} + "
                f"(NOCS: {nocs_result.final_nocs:.2f}/100 * "
                f"Rate: {self.payout_conversion_rate:.2f} * "
                f"Multiplier: {strategic_multiplier:.2f} * "
                f"Ethos: {ethos_coefficient:.2f}) - "
                f"Penalties: {penalties:.2f}"
            )

        # Calculate total compensation
        total_amount = base_amount + variable_amount - penalties

        # Ensure total doesn't go below 0 (floor at 0)
        total_amount = max(0.0, total_amount)

        # Generate compensation event ID
        comp_event_id = f"comp_{uuid.uuid4().hex[:12]}"

        return CompensationEvent(
            comp_event_id=comp_event_id,
            actor_id=actor_id,
            period_id=period_id,
            base_amount=base_amount,
            variable_amount=variable_amount,
            total_amount=total_amount,
            multiplier=strategic_multiplier,
            ethos_coefficient=ethos_coefficient,
            penalties=penalties,
            deferred_accrual=0.0,  # Not implemented yet
            explanation=explanation,
        )

    @staticmethod
    def _calculate_ethos_coefficient(ethos_alignment_score: float) -> float:
        """
        Calculate ethos coefficient based on alignment score.

        Args:
            ethos_alignment_score: Score from 0-100

        Returns:
            Coefficient value (0.0, 0.75, 1.0, or 1.25)
        """
        if ethos_alignment_score >= 90:
            return 1.25
        elif ethos_alignment_score >= 70:
            return 1.0
        elif ethos_alignment_score >= 50:
            return 0.75
        else:
            return 0.0
