"""
Tests for Decision Object and Scoring Models

Tests the 22-field DecisionObject, ValueScores, TrustScores, AlignmentScores,
and RTQL models with comprehensive coverage.
"""

import pytest
from datetime import datetime
from l3_qualification.models import (
    DecisionClass,
    Reversibility,
    TrustTier,
    ValueScores,
    TrustScores,
    AlignmentScores,
    DecisionObject,
    RTQLStage,
    RTQLScores,
    CausalChecks,
    RTQLInput,
    WriteTarget,
)


class TestValueScores:
    """Tests for ValueScores model."""

    def test_gross_value_calculation(self):
        """Test gross value sum of positive dimensions."""
        scores = ValueScores(
            revenue_impact=2,
            cost_efficiency=3,
            time_leverage=2,
            strategic_alignment=4,
            customer_human_benefit=3,
            knowledge_asset_creation=2,
            compounding_potential=3,
            reversibility=2,
        )
        assert scores.gross_value() == 21.0

    def test_penalty_calculation(self):
        """Test penalty sum."""
        scores = ValueScores(
            downside_risk=2,
            execution_drag=3,
            uncertainty=2,
            ethical_misalignment=1,
        )
        assert scores.penalty() == 8.0

    def test_net_value_calculation(self):
        """Test net value = gross - penalty."""
        scores = ValueScores(
            revenue_impact=3,
            cost_efficiency=3,
            time_leverage=2,
            strategic_alignment=3,
            customer_human_benefit=2,
            knowledge_asset_creation=2,
            compounding_potential=2,
            reversibility=2,
            downside_risk=2,
            execution_drag=2,
            uncertainty=1,
            ethical_misalignment=1,
        )
        gross = scores.gross_value()
        penalty = scores.penalty()
        assert scores.net_value() == gross - penalty

    def test_value_classification_high(self):
        """Test high value classification."""
        scores = ValueScores(
            revenue_impact=5,
            cost_efficiency=4,
            time_leverage=4,
            strategic_alignment=4,
            customer_human_benefit=4,
            knowledge_asset_creation=3,
            compounding_potential=3,
            reversibility=3,
        )
        assert scores.value_classification() == "high"

    def test_value_classification_medium(self):
        """Test medium value classification."""
        scores = ValueScores(
            revenue_impact=2,
            cost_efficiency=2,
            time_leverage=2,
            strategic_alignment=2,
            customer_human_benefit=2,
            knowledge_asset_creation=1,
            compounding_potential=1,
            reversibility=2,
        )
        assert scores.value_classification() == "medium"

    def test_value_classification_low(self):
        """Test low value classification."""
        scores = ValueScores(
            revenue_impact=1,
            cost_efficiency=1,
            time_leverage=1,
            strategic_alignment=1,
        )
        assert scores.value_classification() == "low"


class TestTrustScores:
    """Tests for TrustScores model."""

    def test_total_calculation(self):
        """Test total sum of 7 trust dimensions."""
        scores = TrustScores(
            evidence_quality=3,
            logic_integrity=3,
            outcome_history=2,
            context_fit=3,
            stakeholder_clarity=2,
            risk_containment=2,
            auditability=3,
        )
        assert scores.total() == 18

    def test_average_calculation(self):
        """Test average of 7 trust dimensions."""
        scores = TrustScores(
            evidence_quality=5,
            logic_integrity=5,
            outcome_history=5,
            context_fit=5,
            stakeholder_clarity=5,
            risk_containment=5,
            auditability=5,
        )
        assert scores.average() == pytest.approx(5.0)

    def test_tier_mapping_t4(self):
        """Test T4 tier qualification (total >= 30)."""
        scores = TrustScores(
            evidence_quality=5,
            logic_integrity=5,
            outcome_history=4,
            context_fit=4,
            stakeholder_clarity=4,
            risk_containment=4,
            auditability=5,
        )
        assert scores.total() >= 30

    def test_tier_mapping_t0(self):
        """Test T0 tier (total < 10)."""
        scores = TrustScores(
            evidence_quality=1,
            logic_integrity=1,
            outcome_history=1,
            context_fit=1,
            stakeholder_clarity=1,
            risk_containment=1,
            auditability=1,
        )
        assert scores.total() < 10


class TestAlignmentScores:
    """Tests for AlignmentScores model."""

    def test_composite_alignment(self):
        """Test composite alignment score."""
        alignment = AlignmentScores(
            doctrine_alignment=0.8,
            ethos_alignment=0.9,
            first_principles_alignment=0.7,
        )
        # Expected: 0.8 * 0.4 + 0.9 * 0.3 + 0.7 * 0.3 = 0.32 + 0.27 + 0.21 = 0.80
        assert alignment.composite() == pytest.approx(0.80)

    def test_anti_pattern_flags(self):
        """Test anti-pattern flag tracking."""
        alignment = AlignmentScores(
            anti_pattern_flags=[
                "undefined_ownership",
                "decisions_without_auditability",
            ]
        )
        assert len(alignment.anti_pattern_flags) == 2
        assert "undefined_ownership" in alignment.anti_pattern_flags


class TestRTQLScores:
    """Tests for RTQL scoring model."""

    def test_valid_rtql_score(self):
        """Test creation with valid RTQL scores."""
        scores = RTQLScores(
            source_integrity=6,
            exposure_count=5,
            independence=4,
            explainability=8,
            replicability=8,
            adversarial_robustness=6,
            novelty_yield=10,
        )
        assert scores.source_integrity == 6

    def test_invalid_rtql_score_raises(self):
        """Test that invalid RTQL score raises ValueError."""
        with pytest.raises(ValueError, match="not in allowed scores"):
            RTQLScores(source_integrity=7)  # 7 not in allowed set

    def test_allowed_scores_set(self):
        """Test that all allowed scores are in valid set."""
        for score in [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]:
            rtql = RTQLScores(source_integrity=score)
            assert rtql.source_integrity == score


class TestDecisionObject:
    """Tests for 22-field DecisionObject."""

    def test_decision_object_creation(self):
        """Test creation of DecisionObject with all 22 fields."""
        decision = DecisionObject(
            decision_id="DEC-001",
            title="Migrate to Cloud Infrastructure",
            decision_class=DecisionClass.D5,
            owner="John Smith",
            time_horizon="Q4 2026",
            reversibility=Reversibility.R3,
            problem_statement="Current on-prem infra is costly and inflexible",
            requested_action="Evaluate and implement cloud migration",
            context_summary="Growing org needs scalability",
            stakeholders=["ops_team", "cfo", "cto"],
            constraints=["Budget limit: $500K", "Timeline: 6 months"],
            assumptions=["AWS will remain stable", "Team can learn new tools"],
            unknowns=["Vendor lock-in risks", "Long-term cost projections"],
            value_scores=ValueScores(
                revenue_impact=3,
                cost_efficiency=4,
                time_leverage=3,
                strategic_alignment=4,
            ),
            trust_scores=TrustScores(
                evidence_quality=3,
                logic_integrity=3,
                outcome_history=2,
            ),
            alignment_scores=AlignmentScores(
                doctrine_alignment=0.8,
                ethos_alignment=0.7,
                first_principles_alignment=0.75,
            ),
            evidence_refs=[
                "AWS Case Studies",
                "Migration playbook v2.1",
            ],
            required_approvals=["CTO", "CFO"],
            execution_plan="Phase 1: Assessment, Phase 2: Pilot, Phase 3: Full migration",
            monitoring_metric="Cost per compute unit, uptime %, team productivity",
            rollback_trigger="If monthly costs exceed $50K or uptime < 99.9%",
            review_date="2026-10-01",
            current_state="planning",
            actor_role="infrastructure_architect",
        )

        assert decision.decision_id == "DEC-001"
        assert decision.decision_class == DecisionClass.D5
        assert len(decision.stakeholders) == 3
        assert decision.trust_scores.total() >= 0

    def test_decision_object_defaults(self):
        """Test DecisionObject with minimal fields."""
        decision = DecisionObject(
            decision_id="MIN-001",
            title="Simple decision",
            decision_class=DecisionClass.D1,
        )
        assert decision.decision_id == "MIN-001"
        assert decision.owner is None
        assert decision.current_state == "draft"
        assert decision.has_missing_data is False


class TestRTQLInput:
    """Tests for RTQL input model."""

    def test_rtql_input_creation(self):
        """Test RTQL input creation."""
        scores = RTQLScores(
            source_integrity=5,
            exposure_count=4,
            independence=5,
            explainability=8,
            replicability=8,
            adversarial_robustness=6,
            novelty_yield=10,
        )
        causal = CausalChecks(
            reveals_causal_mechanism=True,
            is_irreducible=True,
            survives_authority_removal=True,
            survives_context_shift=True,
        )
        rtql_input = RTQLInput(
            scores=scores,
            causal_checks=causal,
            is_identifiable=True,
            has_provenance=True,
            record_id="REC-001",
        )

        assert rtql_input.scores.source_integrity == 5
        assert rtql_input.causal_checks.reveals_causal_mechanism is True


class TestCausalChecks:
    """Tests for causal mechanism checks."""

    def test_all_causal_checks_pass(self):
        """Test when all 4 causal checks pass."""
        causal = CausalChecks(
            reveals_causal_mechanism=True,
            is_irreducible=True,
            survives_authority_removal=True,
            survives_context_shift=True,
        )
        assert all(
            [
                causal.reveals_causal_mechanism,
                causal.is_irreducible,
                causal.survives_authority_removal,
                causal.survives_context_shift,
            ]
        )

    def test_partial_causal_checks(self):
        """Test when some causal checks fail."""
        causal = CausalChecks(
            reveals_causal_mechanism=True,
            is_irreducible=False,
            survives_authority_removal=True,
            survives_context_shift=False,
        )
        assert causal.reveals_causal_mechanism is True
        assert causal.is_irreducible is False
