"""
Comprehensive tests for Advanced RTQL Classification Engine

Tests cover:
- 9-stage RTQL classification path
- Gate thresholds (qualification and certification)
- Trust multiplier mapping
- Research action generation
- Stage upgrades and upgrade paths
- Causal checks for first-principles candidates
"""

import unittest
import sys
import os

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _PROJECT_ROOT)

from l3_qualification.engines.rtql_advanced import (
    RTQLAdvancedClassifier,
    RTQLGates,
    TRUST_MULTIPLIERS,
    WRITE_TARGET_MAP,
)
from l3_qualification.models.decision_object import (
    RTQLInput,
    RTQLScores,
    CausalChecks,
    RTQLStage,
    WriteTarget,
)


class TestRTQLClassification(unittest.TestCase):
    """Test RTQL classification stages."""

    def setUp(self):
        """Initialize test fixtures."""
        self.classifier = RTQLAdvancedClassifier()

    def test_noise_classification_no_provenance(self):
        """Test NOISE classification when provenance missing."""
        inp = RTQLInput(
            scores=RTQLScores(),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=False,  # No provenance
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.NOISE)
        self.assertFalse(result.passed)
        self.assertIn("provenance", result.blocking_reasons[0].lower())

    def test_noise_classification_not_identifiable(self):
        """Test NOISE classification when not identifiable."""
        inp = RTQLInput(
            scores=RTQLScores(),
            causal_checks=CausalChecks(),
            is_identifiable=False,  # Not identifiable
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.NOISE)
        self.assertFalse(result.passed)

    def test_weak_signal_source_integrity_low(self):
        """Test WEAK_SIGNAL when source_integrity below threshold."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=2,  # < 4
                exposure_count=5,
                independence=5,
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.WEAK_SIGNAL)
        self.assertFalse(result.passed)
        self.assertIn("Source integrity", str(result.blocking_reasons))

    def test_echo_signal_independence_low(self):
        """Test ECHO_SIGNAL when independence below threshold."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=2,  # < 4
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.ECHO_SIGNAL)
        self.assertFalse(result.passed)

    def test_qualified_passes_qual_gate(self):
        """Test QUALIFIED when all qual gates pass."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=5,
                replicability=5,
                adversarial_robustness=5,
                novelty_yield=3,  # Below research-grade
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.CERTIFICATION_GAP)
        self.assertTrue(result.passed)

    def test_certification_gap_fails_explainability(self):
        """Test CERTIFICATION_GAP when explainability fails."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=3,  # < 6
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=5,
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.CERTIFICATION_GAP)
        self.assertTrue(result.passed)  # Qualified but not certified
        self.assertIn("Explainability", str(result.blocking_reasons))

    def test_certified_passes_cert_gate(self):
        """Test CERTIFIED when all cert gates pass."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=6,
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=3,  # Below research-grade
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.CERTIFIED)
        self.assertTrue(result.passed)

    def test_research_grade_high_novelty(self):
        """Test RESEARCH_GRADE when novelty >= 6."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=6,
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=6,  # >= 6
            ),
            causal_checks=CausalChecks(
                reveals_causal_mechanism=False,  # Missing one check
            ),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.RESEARCH_GRADE)
        self.assertTrue(result.passed)
        self.assertIn("Does not reveal causal mechanism", str(result.blocking_reasons))

    def test_first_principles_candidate_all_causal_pass(self):
        """Test FIRST_PRINCIPLES_CANDIDATE when all causal checks pass."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=6,
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=8,
            ),
            causal_checks=CausalChecks(
                reveals_causal_mechanism=True,
                is_irreducible=True,
                survives_authority_removal=True,
                survives_context_shift=True,
            ),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertEqual(result.stage, RTQLStage.FIRST_PRINCIPLES_CANDIDATE)
        self.assertTrue(result.passed)
        self.assertEqual(len(result.blocking_reasons), 0)


class TestRTQLGates(unittest.TestCase):
    """Test gate thresholds."""

    def test_qual_gate_source_integrity_threshold(self):
        """Test qualification gate source integrity threshold."""
        self.assertEqual(RTQLGates.QUAL_GATE["source_integrity"], 4)

    def test_qual_gate_exposure_count_threshold(self):
        """Test qualification gate exposure count threshold."""
        self.assertEqual(RTQLGates.QUAL_GATE["exposure_count"], 3)

    def test_qual_gate_independence_threshold(self):
        """Test qualification gate independence threshold."""
        self.assertEqual(RTQLGates.QUAL_GATE["independence"], 4)

    def test_cert_gate_explainability_threshold(self):
        """Test certification gate explainability threshold."""
        self.assertEqual(RTQLGates.CERT_GATE["explainability"], 6)

    def test_cert_gate_replicability_threshold(self):
        """Test certification gate replicability threshold."""
        self.assertEqual(RTQLGates.CERT_GATE["replicability"], 6)

    def test_cert_gate_adversarial_robustness_threshold(self):
        """Test certification gate adversarial robustness threshold."""
        self.assertEqual(RTQLGates.CERT_GATE["adversarial_robustness"], 6)

    def test_novelty_research_grade_threshold(self):
        """Test research-grade novelty threshold."""
        self.assertEqual(RTQLGates.NOVELTY_RESEARCH_GRADE, 6)


class TestTrustMultipliers(unittest.TestCase):
    """Test trust multiplier mapping."""

    def test_noise_multiplier(self):
        """Test NOISE trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.NOISE], 0.00)

    def test_weak_signal_multiplier(self):
        """Test WEAK_SIGNAL trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.WEAK_SIGNAL], 0.35)

    def test_echo_signal_multiplier(self):
        """Test ECHO_SIGNAL trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.ECHO_SIGNAL], 0.50)

    def test_qualified_multiplier(self):
        """Test QUALIFIED trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.QUALIFIED], 1.00)

    def test_certification_gap_multiplier(self):
        """Test CERTIFICATION_GAP trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.CERTIFICATION_GAP], 0.85)

    def test_certified_multiplier(self):
        """Test CERTIFIED trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.CERTIFIED], 1.15)

    def test_research_grade_multiplier(self):
        """Test RESEARCH_GRADE trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.RESEARCH_GRADE], 1.30)

    def test_first_principles_multiplier(self):
        """Test FIRST_PRINCIPLES_CANDIDATE trust multiplier."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.FIRST_PRINCIPLES_CANDIDATE], 1.50)

    def test_axiom_candidate_multiplier(self):
        """Test AXIOM_CANDIDATE trust multiplier (highest)."""
        self.assertEqual(TRUST_MULTIPLIERS[RTQLStage.AXIOM_CANDIDATE], 2.00)

    def test_all_multipliers_in_result(self):
        """Test that classification result includes correct multiplier."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=6,
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=8,
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        classifier = RTQLAdvancedClassifier()
        result = classifier.classify(inp)

        expected_multiplier = TRUST_MULTIPLIERS[result.stage]
        self.assertEqual(result.trust_multiplier, expected_multiplier)


class TestWriteTargets(unittest.TestCase):
    """Test write target mapping."""

    def test_write_targets_mapped_for_all_stages(self):
        """Test that write targets are mapped for all stages."""
        stages = [
            RTQLStage.NOISE,
            RTQLStage.WEAK_SIGNAL,
            RTQLStage.ECHO_SIGNAL,
            RTQLStage.QUALIFIED,
            RTQLStage.CERTIFICATION_GAP,
            RTQLStage.CERTIFIED,
            RTQLStage.RESEARCH_GRADE,
            RTQLStage.FIRST_PRINCIPLES_CANDIDATE,
            RTQLStage.AXIOM_CANDIDATE,
        ]

        for stage in stages:
            self.assertIn(stage, WRITE_TARGET_MAP)
            target = WRITE_TARGET_MAP[stage]
            self.assertIsInstance(target, WriteTarget)

    def test_noise_writes_to_quarantine(self):
        """Test NOISE writes to QUARANTINE."""
        self.assertEqual(WRITE_TARGET_MAP[RTQLStage.NOISE], WriteTarget.QUARANTINE)

    def test_certified_writes_to_operational(self):
        """Test CERTIFIED writes to OPERATIONAL_REGISTRY."""
        self.assertEqual(
            WRITE_TARGET_MAP[RTQLStage.CERTIFIED],
            WriteTarget.OPERATIONAL_REGISTRY,
        )

    def test_first_principles_writes_to_principles(self):
        """Test FIRST_PRINCIPLES_CANDIDATE writes to PRINCIPLES_REGISTRY."""
        self.assertEqual(
            WRITE_TARGET_MAP[RTQLStage.FIRST_PRINCIPLES_CANDIDATE],
            WriteTarget.PRINCIPLES_REGISTRY,
        )


class TestUpgradePath(unittest.TestCase):
    """Test upgrade path functionality."""

    def setUp(self):
        """Initialize test fixtures."""
        self.classifier = RTQLAdvancedClassifier()

    def test_upgrade_path_from_noise(self):
        """Test upgrade path from NOISE stage."""
        path = self.classifier.get_upgrade_path(RTQLStage.NOISE)

        expected = [
            RTQLStage.WEAK_SIGNAL,
            RTQLStage.ECHO_SIGNAL,
            RTQLStage.QUALIFIED,
            RTQLStage.CERTIFICATION_GAP,
            RTQLStage.CERTIFIED,
            RTQLStage.RESEARCH_GRADE,
            RTQLStage.FIRST_PRINCIPLES_CANDIDATE,
            RTQLStage.AXIOM_CANDIDATE,
        ]

        self.assertEqual(path, expected)

    def test_upgrade_path_from_certified(self):
        """Test upgrade path from CERTIFIED stage."""
        path = self.classifier.get_upgrade_path(RTQLStage.CERTIFIED)

        expected = [
            RTQLStage.RESEARCH_GRADE,
            RTQLStage.FIRST_PRINCIPLES_CANDIDATE,
            RTQLStage.AXIOM_CANDIDATE,
        ]

        self.assertEqual(path, expected)

    def test_upgrade_path_from_axiom(self):
        """Test upgrade path from AXIOM_CANDIDATE (terminal)."""
        path = self.classifier.get_upgrade_path(RTQLStage.AXIOM_CANDIDATE)

        self.assertEqual(path, [])

    def test_can_upgrade_to_next_stage(self):
        """Test that upgrade to next stage is valid."""
        can_upgrade = self.classifier.can_upgrade_to(
            RTQLStage.NOISE, RTQLStage.WEAK_SIGNAL
        )
        self.assertTrue(can_upgrade)

    def test_cannot_skip_stages(self):
        """Test that stage skipping is prevented."""
        can_upgrade = self.classifier.can_upgrade_to(
            RTQLStage.NOISE, RTQLStage.CERTIFIED
        )
        self.assertFalse(can_upgrade)

    def test_cannot_downgrade(self):
        """Test that downgrade is prevented."""
        can_upgrade = self.classifier.can_upgrade_to(
            RTQLStage.CERTIFIED, RTQLStage.QUALIFIED
        )
        self.assertFalse(can_upgrade)


class TestPromoteToAxiom(unittest.TestCase):
    """Test promotion to axiom candidate."""

    def setUp(self):
        """Initialize test fixtures."""
        self.classifier = RTQLAdvancedClassifier()

    def test_promote_first_principles_to_axiom(self):
        """Test promoting first-principles candidate to axiom."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=6,
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=8,
            ),
            causal_checks=CausalChecks(
                reveals_causal_mechanism=True,
                is_irreducible=True,
                survives_authority_removal=True,
                survives_context_shift=True,
            ),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)
        self.assertEqual(result.stage, RTQLStage.FIRST_PRINCIPLES_CANDIDATE)

        # Promote to axiom
        promoted = self.classifier.promote_to_axiom(result)

        self.assertEqual(promoted.stage, RTQLStage.AXIOM_CANDIDATE)
        self.assertEqual(
            promoted.trust_multiplier,
            TRUST_MULTIPLIERS[RTQLStage.AXIOM_CANDIDATE],
        )
        self.assertEqual(
            promoted.write_target, WRITE_TARGET_MAP[RTQLStage.AXIOM_CANDIDATE]
        )

    def test_promote_non_first_principles_unchanged(self):
        """Test that promoting non-first-principles stage doesn't change it."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=6,
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=3,  # Below research-grade
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)
        self.assertEqual(result.stage, RTQLStage.CERTIFIED)

        # Attempt to promote
        promoted = self.classifier.promote_to_axiom(result)

        # Should remain CERTIFIED
        self.assertEqual(promoted.stage, RTQLStage.CERTIFIED)


class TestResearchActions(unittest.TestCase):
    """Test research action generation."""

    def setUp(self):
        """Initialize test fixtures."""
        self.classifier = RTQLAdvancedClassifier()

    def test_research_actions_for_noise(self):
        """Test that NOISE stage generates discard action."""
        inp = RTQLInput(
            scores=RTQLScores(),
            causal_checks=CausalChecks(),
            is_identifiable=False,
            has_provenance=False,
        )

        result = self.classifier.classify(inp)

        self.assertGreater(len(result.research_actions), 0)
        self.assertTrue(
            any("discard" in action.lower() for action in result.research_actions)
        )

    def test_research_actions_for_weak_signal(self):
        """Test research actions for WEAK_SIGNAL."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=2,  # Gap
                exposure_count=5,
                independence=5,
            ),
            causal_checks=CausalChecks(),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertGreater(len(result.research_actions), 0)
        self.assertTrue(
            any("source_integrity" in action for action in result.research_actions)
        )

    def test_research_actions_for_research_grade(self):
        """Test research actions include novelty gap for research-grade."""
        inp = RTQLInput(
            scores=RTQLScores(
                source_integrity=5,
                exposure_count=5,
                independence=5,
                explainability=6,
                replicability=6,
                adversarial_robustness=6,
                novelty_yield=3,  # Gap
            ),
            causal_checks=CausalChecks(
                reveals_causal_mechanism=False,
            ),
            is_identifiable=True,
            has_provenance=True,
        )

        result = self.classifier.classify(inp)

        self.assertGreater(len(result.research_actions), 0)


if __name__ == "__main__":
    unittest.main()
