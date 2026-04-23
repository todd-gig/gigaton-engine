"""
Advanced RTQL Classification Engine (9-Stage)

Implements the Recursive Trust Qualification Loop (RTQL) classification pipeline
with 9 stages, gate thresholds, research action routing, and upgrade path validation.

Stage progression:
    noise → weak_signal → echo_signal → qualified →
    certification_gap → certified → research_grade →
    first_principles_candidate → axiom_candidate
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ..models import (
    RTQLStage,
    RTQLScores,
    CausalChecks,
    RTQLInput,
    RTQLResult,
    WriteTarget,
)


# ─────────────────────────────────────────────
# GATE THRESHOLDS
# ─────────────────────────────────────────────

class RTQLGates:
    """RTQL gate thresholds for qualification and certification."""

    # Qualification gate (Gate 1-3)
    QUAL_GATE = {
        "source_integrity": 4,
        "exposure_count": 3,
        "independence": 4,
    }

    # Certification gate (Gate 4-6)
    CERT_GATE = {
        "explainability": 6,
        "replicability": 6,
        "adversarial_robustness": 6,
    }

    # Research-grade novelty threshold
    NOVELTY_RESEARCH_GRADE = 6

    # Pre-qualification thresholds
    NOISE_THRESHOLD = 1
    WEAK_SIGNAL_THRESHOLD = 2


# ─────────────────────────────────────────────
# TRUST MULTIPLIERS & WRITE TARGETS
# ─────────────────────────────────────────────

TRUST_MULTIPLIERS = {
    RTQLStage.NOISE: 0.00,
    RTQLStage.WEAK_SIGNAL: 0.35,
    RTQLStage.ECHO_SIGNAL: 0.50,
    RTQLStage.QUALIFIED: 1.00,
    RTQLStage.CERTIFICATION_GAP: 0.85,
    RTQLStage.CERTIFIED: 1.15,
    RTQLStage.RESEARCH_GRADE: 1.30,
    RTQLStage.FIRST_PRINCIPLES_CANDIDATE: 1.50,
    RTQLStage.AXIOM_CANDIDATE: 2.00,
}

WRITE_TARGET_MAP = {
    RTQLStage.NOISE: WriteTarget.QUARANTINE,
    RTQLStage.WEAK_SIGNAL: WriteTarget.STAGING,
    RTQLStage.ECHO_SIGNAL: WriteTarget.STAGING,
    RTQLStage.QUALIFIED: WriteTarget.CANDIDATE_REGISTRY,
    RTQLStage.CERTIFICATION_GAP: WriteTarget.CANDIDATE_REGISTRY,
    RTQLStage.CERTIFIED: WriteTarget.OPERATIONAL_REGISTRY,
    RTQLStage.RESEARCH_GRADE: WriteTarget.INSIGHT_REGISTRY,
    RTQLStage.FIRST_PRINCIPLES_CANDIDATE: WriteTarget.PRINCIPLES_REGISTRY,
    RTQLStage.AXIOM_CANDIDATE: WriteTarget.AXIOM_REVIEW_QUEUE,
}


# ─────────────────────────────────────────────
# RESEARCH ACTION GENERATION
# ─────────────────────────────────────────────

class RTQLResearchActions:
    """Generate research actions for failed gates."""

    @staticmethod
    def _qual_actions(scores: RTQLScores) -> List[str]:
        """Generate actions for qualification gate failures."""
        actions = []

        if scores.source_integrity < RTQLGates.QUAL_GATE["source_integrity"]:
            gap = RTQLGates.QUAL_GATE["source_integrity"] - scores.source_integrity
            actions.append(
                f"QUAL-GATE | source_integrity: score {scores.source_integrity} is "
                f"{gap} point(s) below threshold. "
                "Action: Identify primary sources; cross-validate provenance."
            )

        if scores.exposure_count < RTQLGates.QUAL_GATE["exposure_count"]:
            gap = RTQLGates.QUAL_GATE["exposure_count"] - scores.exposure_count
            actions.append(
                f"QUAL-GATE | exposure_count: score {scores.exposure_count} is "
                f"{gap} point(s) below threshold. "
                "Action: Seek additional independent observations or trials."
            )

        if scores.independence < RTQLGates.QUAL_GATE["independence"]:
            gap = RTQLGates.QUAL_GATE["independence"] - scores.independence
            actions.append(
                f"QUAL-GATE | independence: score {scores.independence} is "
                f"{gap} point(s) below threshold. "
                "Action: Source evidence from independent organisations/teams."
            )

        return actions

    @staticmethod
    def _cert_actions(scores: RTQLScores) -> List[str]:
        """Generate actions for certification gate failures."""
        actions = []

        if scores.explainability < RTQLGates.CERT_GATE["explainability"]:
            gap = RTQLGates.CERT_GATE["explainability"] - scores.explainability
            actions.append(
                f"CERT-GATE | explainability: score {scores.explainability} is "
                f"{gap} point(s) below threshold. "
                "Action: Document the mechanism step-by-step; produce explanatory model."
            )

        if scores.replicability < RTQLGates.CERT_GATE["replicability"]:
            gap = RTQLGates.CERT_GATE["replicability"] - scores.replicability
            actions.append(
                f"CERT-GATE | replicability: score {scores.replicability} is "
                f"{gap} point(s) below threshold. "
                "Action: Design and run controlled replication studies."
            )

        if scores.adversarial_robustness < RTQLGates.CERT_GATE["adversarial_robustness"]:
            gap = (
                RTQLGates.CERT_GATE["adversarial_robustness"]
                - scores.adversarial_robustness
            )
            actions.append(
                f"CERT-GATE | adversarial_robustness: score {scores.adversarial_robustness} is "
                f"{gap} point(s) below threshold. "
                "Action: Stress-test claim under adversarial conditions; invite critique."
            )

        return actions

    @staticmethod
    def _novelty_actions(scores: RTQLScores) -> List[str]:
        """Generate actions for research-grade novelty gap."""
        actions = []

        if scores.novelty_yield < RTQLGates.NOVELTY_RESEARCH_GRADE:
            gap = RTQLGates.NOVELTY_RESEARCH_GRADE - scores.novelty_yield
            actions.append(
                f"RESEARCH-GRADE | novelty_yield: score {scores.novelty_yield} is "
                f"{gap} point(s) below threshold. "
                "Action: Articulate new understanding; compare against literature."
            )

        return actions

    @staticmethod
    def _causal_actions(causal: CausalChecks) -> List[str]:
        """Generate actions for first-principles causal gaps."""
        actions = []

        action_hints = {
            "reveals_causal_mechanism": (
                "Map the causal pathway; identify mediating variables."
            ),
            "is_irreducible": (
                "Attempt to decompose further; confirm irreducibility through elimination."
            ),
            "survives_authority_removal": (
                "Test whether the claim holds when all authority references are stripped."
            ),
            "survives_context_shift": (
                "Apply the claim across multiple distinct contexts; document failures."
            ),
        }

        causal_map = {
            "reveals_causal_mechanism": causal.reveals_causal_mechanism,
            "is_irreducible": causal.is_irreducible,
            "survives_authority_removal": causal.survives_authority_removal,
            "survives_context_shift": causal.survives_context_shift,
        }

        for check, passed in causal_map.items():
            if not passed:
                actions.append(
                    f"FIRST-PRINCIPLES | {check}: not satisfied. "
                    f"Action: {action_hints[check]}"
                )

        return actions

    @staticmethod
    def generate(stage: RTQLStage, scores: RTQLScores, causal: CausalChecks) -> List[str]:
        """Generate research actions for given stage and scores."""
        actions = []

        if stage == RTQLStage.NOISE:
            actions.append(
                "Discard or seek entirely new data sources — all dimensions at noise floor."
            )
            return actions

        # Qualification gate failures
        actions.extend(RTQLResearchActions._qual_actions(scores))

        # Certification gate failures (only if qualified)
        if RTQLResearchActions._passes_qual_gate(scores):
            actions.extend(RTQLResearchActions._cert_actions(scores))

            # Novelty gap for certified
            if stage in (RTQLStage.CERTIFIED, RTQLStage.RESEARCH_GRADE):
                actions.extend(RTQLResearchActions._novelty_actions(scores))

        # First-principles causal gaps
        if stage == RTQLStage.RESEARCH_GRADE:
            actions.extend(RTQLResearchActions._causal_actions(causal))

        return actions

    @staticmethod
    def _passes_qual_gate(scores: RTQLScores) -> bool:
        """Check if qualification gate is passed."""
        return (
            scores.source_integrity >= RTQLGates.QUAL_GATE["source_integrity"]
            and scores.exposure_count >= RTQLGates.QUAL_GATE["exposure_count"]
            and scores.independence >= RTQLGates.QUAL_GATE["independence"]
        )

    @staticmethod
    def _passes_cert_gate(scores: RTQLScores) -> bool:
        """Check if certification gate is passed."""
        return (
            scores.explainability >= RTQLGates.CERT_GATE["explainability"]
            and scores.replicability >= RTQLGates.CERT_GATE["replicability"]
            and scores.adversarial_robustness >= RTQLGates.CERT_GATE["adversarial_robustness"]
        )

    @staticmethod
    def _all_causal_checks(causal: CausalChecks) -> bool:
        """Check if all causal mechanism checks pass."""
        return (
            causal.reveals_causal_mechanism
            and causal.is_irreducible
            and causal.survives_authority_removal
            and causal.survives_context_shift
        )


# ─────────────────────────────────────────────
# RTQL CLASSIFIER
# ─────────────────────────────────────────────

class RTQLAdvancedClassifier:
    """
    Advanced RTQL classifier implementing 9-stage hierarchy with gate validation,
    research action routing, and upgrade path tracking.
    """

    def classify(self, inp: RTQLInput) -> RTQLResult:
        """
        Classify input through RTQL gates.

        Returns RTQLResult with stage, passed flag, blocking reasons, trust multiplier,
        write target, and research actions.
        """
        result = RTQLResult()
        scores = inp.scores
        causal = inp.causal_checks
        blocking = []

        # Gate 0: Identifiability & Provenance
        if not inp.is_identifiable or not inp.has_provenance:
            result.stage = RTQLStage.NOISE
            blocking.append("Input is not identifiable or lacks provenance")
            result.blocking_reasons = blocking
            result.trust_multiplier = TRUST_MULTIPLIERS[result.stage]
            result.write_target = WRITE_TARGET_MAP[result.stage]
            result.research_actions = RTQLResearchActions.generate(
                result.stage, scores, causal
            )
            return result

        # Gate 1: Source Integrity (>= 4)
        if scores.source_integrity < RTQLGates.QUAL_GATE["source_integrity"]:
            result.stage = RTQLStage.WEAK_SIGNAL
            blocking.append(f"Source integrity {scores.source_integrity} < 4")

        # Gate 2: Exposure Count (>= 3)
        if scores.exposure_count < RTQLGates.QUAL_GATE["exposure_count"]:
            if result.stage == RTQLStage.NOISE:
                result.stage = RTQLStage.WEAK_SIGNAL
            blocking.append(f"Exposure count {scores.exposure_count} < 3")

        # Gate 3: Independence (>= 4)
        if scores.independence < RTQLGates.QUAL_GATE["independence"]:
            if not blocking or result.stage == RTQLStage.NOISE:
                result.stage = RTQLStage.ECHO_SIGNAL
            blocking.append(f"Independence {scores.independence} < 4")

        # If any qualification gate failed, stop here
        if blocking:
            result.blocking_reasons = blocking
            result.trust_multiplier = TRUST_MULTIPLIERS[result.stage]
            result.write_target = WRITE_TARGET_MAP[result.stage]
            result.research_actions = RTQLResearchActions.generate(
                result.stage, scores, causal
            )
            return result

        # Qualification passed — test certification gates

        cert_gaps = []

        # Gate 4: Explainability (>= 6)
        if scores.explainability < RTQLGates.CERT_GATE["explainability"]:
            cert_gaps.append(f"Explainability {scores.explainability} < 6")

        # Gate 5: Replicability (>= 6)
        if scores.replicability < RTQLGates.CERT_GATE["replicability"]:
            cert_gaps.append(f"Replicability {scores.replicability} < 6")

        # Gate 6: Adversarial Robustness (>= 6)
        if scores.adversarial_robustness < RTQLGates.CERT_GATE["adversarial_robustness"]:
            cert_gaps.append(
                f"Adversarial robustness {scores.adversarial_robustness} < 6"
            )

        if cert_gaps:
            result.stage = RTQLStage.CERTIFICATION_GAP
            result.blocking_reasons = cert_gaps
            result.trust_multiplier = TRUST_MULTIPLIERS[result.stage]
            result.write_target = WRITE_TARGET_MAP[result.stage]
            result.research_actions = RTQLResearchActions.generate(
                result.stage, scores, causal
            )
            result.passed = True  # Qualified but not certified
            return result

        # Certification passed — test research-grade novelty

        if scores.novelty_yield < RTQLGates.NOVELTY_RESEARCH_GRADE:
            # Certified but not novel enough
            result.stage = RTQLStage.CERTIFIED
            result.passed = True
            result.trust_multiplier = TRUST_MULTIPLIERS[result.stage]
            result.write_target = WRITE_TARGET_MAP[result.stage]
            result.research_actions = RTQLResearchActions.generate(
                result.stage, scores, causal
            )
            return result

        # Research-grade passed — test for first-principles

        fp_gaps = []
        if not causal.reveals_causal_mechanism:
            fp_gaps.append("Does not reveal causal mechanism")
        if not causal.is_irreducible:
            fp_gaps.append("Not irreducible — can be decomposed further")
        if not causal.survives_authority_removal:
            fp_gaps.append("Does not survive authority removal")
        if not causal.survives_context_shift:
            fp_gaps.append("Does not survive context shift")

        if fp_gaps:
            result.stage = RTQLStage.RESEARCH_GRADE
            result.passed = True
            result.blocking_reasons = fp_gaps
            result.trust_multiplier = TRUST_MULTIPLIERS[result.stage]
            result.write_target = WRITE_TARGET_MAP[result.stage]
            result.research_actions = RTQLResearchActions.generate(
                result.stage, scores, causal
            )
            return result

        # All gates passed — first principles candidate
        result.stage = RTQLStage.FIRST_PRINCIPLES_CANDIDATE
        result.passed = True
        result.trust_multiplier = TRUST_MULTIPLIERS[result.stage]
        result.write_target = WRITE_TARGET_MAP[result.stage]
        return result

    def promote_to_axiom(self, result: RTQLResult) -> RTQLResult:
        """
        Promote first_principles_candidate to axiom_candidate.
        Returns updated result.
        """
        if result.stage == RTQLStage.FIRST_PRINCIPLES_CANDIDATE:
            result.stage = RTQLStage.AXIOM_CANDIDATE
            result.trust_multiplier = TRUST_MULTIPLIERS[result.stage]
            result.write_target = WRITE_TARGET_MAP[result.stage]
        return result

    def get_upgrade_path(self, current_stage: RTQLStage) -> List[RTQLStage]:
        """
        Get valid upgrade path from current stage.

        Returns list of achievable stages in order of progression.
        """
        stage_order = [
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

        try:
            idx = stage_order.index(current_stage)
            return stage_order[idx + 1 :]
        except ValueError:
            return []

    def can_upgrade_to(
        self, current_stage: RTQLStage, target_stage: RTQLStage
    ) -> bool:
        """Check if upgrade from current to target stage is valid (no skipping)."""
        upgrade_path = self.get_upgrade_path(current_stage)
        # Can only upgrade to the NEXT stage, not skip ahead
        return len(upgrade_path) > 0 and upgrade_path[0] == target_stage
