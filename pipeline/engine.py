"""
GigatonEngine — unified L1→L3→L4 pipeline orchestrator.

Flow:
  1. L1: Score prospect → ProspectValueAssessment
  2. L1→L3 Bridge: Convert assessment to decision dict
  3. L3: Qualify decision → Decision (verdict, certs, priority)
  4. L4: Score interactions → ActionBenchmarks → NOCS → Compensation

The engine produces a PipelineResult containing the complete
prospect-to-profitability chain.
"""
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Ensure parent is on path for cross-module imports
_ENGINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _ENGINE_ROOT)

from l1_sensing.models.prospect import ProspectProfile
from l1_sensing.models.inference import InferenceRecord
from l1_sensing.models.value_assessment import ProspectValueAssessment
from l1_sensing.engines.prospect_value_engine import ProspectValueEngine

from l3_qualification.engine import QualificationEngine

from l4_execution.models.interaction import InteractionEvent
from l4_execution.models.role_profile import RoleProfile, ROLE_PROFILES
from l4_execution.engines.interaction_scorer import InteractionScorer
from l4_execution.engines.nocs_engine import NOCSEngine, NOCSResult
from l4_execution.engines.compensation_engine import CompensationEngine


@dataclass
class InteractionResult:
    """Result for a single interaction through L4."""
    interaction_id: str
    channel: str
    nocs: NOCSResult
    compensation_total: float
    compensation_variable: float
    ethos_coefficient: float
    explanation: str


@dataclass
class PipelineResult:
    """Complete L1→L3→L4 pipeline result."""

    # L1 outputs
    prospect_id: str
    prospect_name: str
    prospect_assessment: ProspectValueAssessment

    # L3 outputs
    decision_id: str
    verdict: str
    value_score: float
    trust_score: float
    rtql_stage: int
    rtql_multiplier: float
    priority_score: float
    certificates: Dict[str, bool] = field(default_factory=dict)
    blocking_gates: List[str] = field(default_factory=list)

    # L4 outputs (per-interaction)
    interaction_results: List[InteractionResult] = field(default_factory=list)

    # Aggregates
    total_compensation: float = 0.0
    avg_nocs: float = 0.0
    interaction_count: int = 0

    def summary(self) -> Dict[str, Any]:
        """Return a summary dict for reporting."""
        return {
            "prospect": {
                "id": self.prospect_id,
                "name": self.prospect_name,
                "fit_score": round(self.prospect_assessment.total, 2),
                "need": round(self.prospect_assessment.need, 2),
                "service_fit": round(self.prospect_assessment.service_fit, 2),
                "readiness": round(self.prospect_assessment.readiness, 2),
                "confidence": round(self.prospect_assessment.confidence, 2),
            },
            "qualification": {
                "decision_id": self.decision_id,
                "verdict": self.verdict,
                "value_score": round(self.value_score, 3),
                "trust_score": round(self.trust_score, 3),
                "rtql": f"stage {self.rtql_stage}/7 (×{self.rtql_multiplier:.2f})",
                "priority": round(self.priority_score, 3),
                "certificates": self.certificates,
                "blocking_gates": self.blocking_gates,
            },
            "execution": {
                "interaction_count": self.interaction_count,
                "avg_nocs": round(self.avg_nocs, 2),
                "total_compensation": round(self.total_compensation, 2),
            },
        }


class GigatonEngine:
    """
    Unified L1→L3→L4 pipeline.

    Usage:
        engine = GigatonEngine()
        result = engine.run(prospect, inferences, interactions, role_key="sales_operator")
    """

    def __init__(self, payout_rate: float = 50.0):
        self.l3 = QualificationEngine()
        self.comp_engine = CompensationEngine(payout_conversion_rate=payout_rate)

    def run(
        self,
        prospect: ProspectProfile,
        inferences: List[InferenceRecord],
        interactions: List[InteractionEvent],
        role_key: str = "sales_operator",
        base_compensation: float = 5000.0,
        strategic_multiplier: float = 1.0,
    ) -> PipelineResult:
        """
        Run the full L1→L3→L4 pipeline.

        Args:
            prospect: ProspectProfile from L1
            inferences: List of InferenceRecords from signal analysis
            interactions: List of InteractionEvents from touchpoints
            role_key: Role profile key for NOCS weighting
            base_compensation: Base compensation amount for the period
            strategic_multiplier: Strategy multiplier (1.0-2.0)

        Returns:
            PipelineResult with complete scoring chain
        """
        # ── L1: SENSING ──────────────────────────────────────────
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # ── L1→L3 BRIDGE ─────────────────────────────────────────
        decision_dict = ProspectValueEngine.prospect_to_decision(
            prospect.prospect_id, assessment, prospect
        )

        # ── L3: QUALIFICATION ─────────────────────────────────────
        decision = self.l3.evaluate(decision_dict)

        # ── L4: EXECUTION ─────────────────────────────────────────
        role = ROLE_PROFILES.get(role_key)
        if role is None:
            role = RoleProfile.create_default(role_key, role_key.replace("_", " ").title())

        interaction_results = []
        total_nocs = 0.0
        total_comp = 0.0

        for interaction in interactions:
            # Score interaction → ActionBenchmark
            benchmark = InteractionScorer.score(interaction)

            # Compute NOCS
            nocs = NOCSEngine.calculate(benchmark, role)

            # Compute compensation
            comp = self.comp_engine.calculate(
                base_amount=base_compensation / max(len(interactions), 1),
                nocs_result=nocs,
                strategic_multiplier=strategic_multiplier,
                ethos_alignment_score=benchmark.ethos_alignment,
                actor_id=interaction.entity_id,
                period_id=f"period_{prospect.prospect_id}",
            )

            interaction_results.append(InteractionResult(
                interaction_id=interaction.interaction_id,
                channel=interaction.channel,
                nocs=nocs,
                compensation_total=comp.total_amount,
                compensation_variable=comp.variable_amount,
                ethos_coefficient=comp.ethos_coefficient,
                explanation=comp.explanation,
            ))

            total_nocs += nocs.final_nocs
            total_comp += comp.total_amount

        avg_nocs = total_nocs / max(len(interactions), 1)

        # ── ASSEMBLE RESULT ───────────────────────────────────────
        return PipelineResult(
            prospect_id=prospect.prospect_id,
            prospect_name=prospect.official_name,
            prospect_assessment=assessment,
            decision_id=decision.decision_id,
            verdict=decision.verdict.value,
            value_score=decision.value_score,
            trust_score=decision.trust_score,
            rtql_stage=decision.rtql_stage,
            rtql_multiplier=decision.rtql_multiplier,
            priority_score=decision.priority_score,
            certificates={
                "QC": decision.qc_pass,
                "VC": decision.vc_pass,
                "TC": decision.tc_pass,
                "EC": decision.ec_pass,
            },
            blocking_gates=decision.blocking_gates,
            interaction_results=interaction_results,
            total_compensation=total_comp,
            avg_nocs=avg_nocs,
            interaction_count=len(interactions),
        )

    def run_l1_only(
        self,
        prospect: ProspectProfile,
        inferences: List[InferenceRecord],
    ) -> ProspectValueAssessment:
        """Run L1 sensing only — prospect scoring without qualification."""
        return ProspectValueEngine.score_prospect(prospect, inferences)

    def run_l1_l3(
        self,
        prospect: ProspectProfile,
        inferences: List[InferenceRecord],
    ) -> dict:
        """Run L1→L3 — prospect scoring + qualification, no execution."""
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)
        decision_dict = ProspectValueEngine.prospect_to_decision(
            prospect.prospect_id, assessment, prospect
        )
        decision = self.l3.evaluate(decision_dict)
        return {
            "assessment": assessment,
            "decision": decision,
        }
