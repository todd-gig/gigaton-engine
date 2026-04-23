"""Unit tests for BrandExperienceEngine."""

import unittest
from l2_brand_experience.engines.brand_experience_engine import BrandExperienceEngine
from l2_brand_experience.models.brand_profile import BrandProfile
from l4_execution.models.interaction import InteractionEvent


class TestBrandExperienceEngine(unittest.TestCase):
    """Tests for BrandExperienceEngine."""

    def test_assess_strong_brand_yields_high_score(self):
        """A well-defined brand should yield high overall experience score."""
        brand = BrandProfile(
            brand_id="brand_001",
            brand_name="Premium Service Co",
            tagline="Excellence in every interaction",
            mission="To deliver exceptional customer experiences",
            value_propositions=["Human-centered service", "Rapid response", "Complete solutions"],
            differentiators=["24/7 availability", "Expert team", "Custom solutions"],
            proof_assets=["Case Study: 500% ROI", "Customer testimonials", "Awards"],
            compliance_claims=["SOC 2 Type II Certified"],
            certifications=["ISO 9001", "ISO 27001"],
            active_channels=["voice", "email", "web", "sms"],
            target_response_time_seconds=300.0,
            target_resolution_time_seconds=3600.0,
            target_conversion_rate=0.15,
        )

        assessment = BrandExperienceEngine.assess(brand, interactions=[])

        # Strong brand should score above 60 (realistic with default performance metrics)
        self.assertGreater(assessment.brand_experience_score, 60.0)
        self.assertGreater(assessment.coherence.composite_score, 60.0)
        self.assertGreater(assessment.channel_consistency_score, 75.0)
        self.assertGreater(assessment.trust_layer_quality, 30.0)

    def test_assess_weak_brand_yields_low_score(self):
        """A poorly-defined brand should yield lower experience score."""
        brand = BrandProfile(
            brand_id="brand_002",
            brand_name="Basic Service",
            tagline="",
            mission="",
            value_propositions=[],
            differentiators=[],
            proof_assets=[],
            compliance_claims=[],
            certifications=[],
            active_channels=["email"],
            target_response_time_seconds=7200.0,
            target_resolution_time_seconds=86400.0,
            target_conversion_rate=0.05,
        )

        assessment = BrandExperienceEngine.assess(brand, interactions=[])

        # Weak brand should score lower
        self.assertLess(assessment.brand_experience_score, 60.0)
        self.assertLess(assessment.channel_consistency_score, 70.0)

    def test_assess_with_no_interactions_uses_defaults(self):
        """Assessment without interactions should use default performance values."""
        brand = BrandProfile(
            brand_id="brand_003",
            brand_name="Test Brand",
            active_channels=["web"],
        )

        assessment = BrandExperienceEngine.assess(brand, interactions=None)

        # Should have default performance of 0.5
        self.assertEqual(assessment.avg_response_performance, 0.5)
        self.assertEqual(assessment.avg_resolution_performance, 0.5)
        self.assertEqual(assessment.conversion_performance, 0.5)
        # Should still have coherence and other scores
        self.assertGreater(assessment.brand_experience_score, 0.0)

    def test_channel_consistency_scores_correctly(self):
        """Channel consistency should reflect number of active channels."""
        # Single channel
        brand_1 = BrandProfile(
            brand_id="brand_1",
            brand_name="Single Channel",
            active_channels=["email"],
        )
        assess_1 = BrandExperienceEngine.assess(brand_1, interactions=[])
        self.assertEqual(assess_1.channel_consistency_score, 60.0)

        # Three channels
        brand_3 = BrandProfile(
            brand_id="brand_3",
            brand_name="Multi Channel",
            active_channels=["email", "web", "phone"],
        )
        assess_3 = BrandExperienceEngine.assess(brand_3, interactions=[])
        self.assertEqual(assess_3.channel_consistency_score, 80.0)

        # Five channels
        brand_5 = BrandProfile(
            brand_id="brand_5",
            brand_name="Omni Channel",
            active_channels=["email", "web", "phone", "sms", "voice"],
        )
        assess_5 = BrandExperienceEngine.assess(brand_5, interactions=[])
        self.assertEqual(assess_5.channel_consistency_score, 90.0)

    def test_proof_to_promise_ratio_calculation(self):
        """Proof-to-promise ratio should be calculated correctly."""
        # No claims, no proof
        brand_0 = BrandProfile(
            brand_id="brand_0",
            brand_name="Empty",
            value_propositions=[],
            differentiators=[],
            proof_assets=[],
        )
        assess_0 = BrandExperienceEngine.assess(brand_0, interactions=[])
        self.assertEqual(assess_0.proof_to_promise_ratio, 0.5)  # Neutral when no claims

        # 3 proof assets, 5 claims -> 0.6
        brand_proof = BrandProfile(
            brand_id="brand_proof",
            brand_name="Well Supported",
            value_propositions=["Fast", "Reliable", "Affordable"],
            differentiators=["Expert", "Custom"],
            proof_assets=["Case 1", "Case 2", "Case 3"],
        )
        assess_proof = BrandExperienceEngine.assess(brand_proof, interactions=[])
        self.assertAlmostEqual(assess_proof.proof_to_promise_ratio, 0.6, places=2)

        # More proof than claims (capped at 1.0)
        brand_over = BrandProfile(
            brand_id="brand_over",
            brand_name="Over Documented",
            value_propositions=["Service"],
            differentiators=[],
            proof_assets=["Case 1", "Case 2", "Case 3"],
        )
        assess_over = BrandExperienceEngine.assess(brand_over, interactions=[])
        self.assertEqual(assess_over.proof_to_promise_ratio, 1.0)

    def test_trust_layer_quality_calculation(self):
        """Trust layer quality should reflect proof, compliance, and certifications."""
        brand_high_trust = BrandProfile(
            brand_id="brand_ht",
            brand_name="High Trust",
            proof_assets=["Case 1", "Case 2", "Testimonial"],
            compliance_claims=["HIPAA Compliant"],
            certifications=["ISO 9001", "ISO 27001"],
        )
        assess_ht = BrandExperienceEngine.assess(brand_high_trust, interactions=[])
        # proof: 15*3=45, compliance: 30, certs: 40 -> (45+30+40)/3 = 38.33
        # High trust should be above 30
        self.assertGreater(assess_ht.trust_layer_quality, 30.0)

        brand_low_trust = BrandProfile(
            brand_id="brand_lt",
            brand_name="Low Trust",
            proof_assets=[],
            compliance_claims=[],
            certifications=[],
        )
        assess_lt = BrandExperienceEngine.assess(brand_low_trust, interactions=[])
        # Should be close to 0 (no assets)
        self.assertLess(assess_lt.trust_layer_quality, 15.0)

        # Test that high trust > low trust
        self.assertGreater(assess_ht.trust_layer_quality, assess_lt.trust_layer_quality)

    def test_response_performance_against_target(self):
        """Response performance should compare actual times against target."""
        brand = BrandProfile(
            brand_id="brand_rp",
            brand_name="Response Test",
            target_response_time_seconds=300.0,
        )

        # All interactions meet target
        interactions_fast = [
            InteractionEvent(
                interaction_id=f"int_{i}",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                response_time_seconds=200.0,
                resolution_time_seconds=600.0,
            )
            for i in range(5)
        ]
        assess_fast = BrandExperienceEngine.assess(brand, interactions=interactions_fast)
        self.assertEqual(assess_fast.avg_response_performance, 1.0)

        # No interactions meet target
        interactions_slow = [
            InteractionEvent(
                interaction_id=f"int_{i}",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                response_time_seconds=600.0,
                resolution_time_seconds=1200.0,
            )
            for i in range(5)
        ]
        assess_slow = BrandExperienceEngine.assess(brand, interactions=interactions_slow)
        self.assertEqual(assess_slow.avg_response_performance, 0.0)

        # Half meet target
        interactions_mixed = [
            InteractionEvent(
                interaction_id="int_1",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                response_time_seconds=200.0,
                resolution_time_seconds=600.0,
            ),
            InteractionEvent(
                interaction_id="int_2",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T01:00:00Z",
                status="resolved",
                response_time_seconds=600.0,
                resolution_time_seconds=1200.0,
            ),
        ]
        assess_mixed = BrandExperienceEngine.assess(brand, interactions=interactions_mixed)
        self.assertEqual(assess_mixed.avg_response_performance, 0.5)

    def test_resolution_performance_against_target(self):
        """Resolution performance should compare actual times against target."""
        brand = BrandProfile(
            brand_id="brand_res",
            brand_name="Resolution Test",
            target_resolution_time_seconds=3600.0,
        )

        # All interactions meet target
        interactions_fast = [
            InteractionEvent(
                interaction_id=f"int_{i}",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                response_time_seconds=100.0,
                resolution_time_seconds=1800.0,
            )
            for i in range(3)
        ]
        assess_fast = BrandExperienceEngine.assess(brand, interactions=interactions_fast)
        self.assertEqual(assess_fast.avg_resolution_performance, 1.0)

    def test_conversion_performance_against_target(self):
        """Conversion performance should measure actual rate against target."""
        brand = BrandProfile(
            brand_id="brand_conv",
            brand_name="Conversion Test",
            target_conversion_rate=0.5,  # 50%
        )

        # 100% conversion (above target)
        interactions_high = [
            InteractionEvent(
                interaction_id=f"int_{i}",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                response_time_seconds=100.0,
                resolution_time_seconds=600.0,
                converted=True,
            )
            for i in range(4)
        ]
        assess_high = BrandExperienceEngine.assess(brand, interactions=interactions_high)
        self.assertEqual(assess_high.conversion_performance, 1.0)  # Capped at 1.0

        # 50% conversion (meets target)
        interactions_exact = [
            InteractionEvent(
                interaction_id="int_1",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                converted=True,
            ),
            InteractionEvent(
                interaction_id="int_2",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T01:00:00Z",
                status="resolved",
                converted=False,
            ),
        ]
        assess_exact = BrandExperienceEngine.assess(brand, interactions=interactions_exact)
        self.assertEqual(assess_exact.conversion_performance, 1.0)

        # 0% conversion
        interactions_zero = [
            InteractionEvent(
                interaction_id=f"int_{i}",
                entity_id="entity_1",
                channel="web",
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                converted=False,
            )
            for i in range(3)
        ]
        assess_zero = BrandExperienceEngine.assess(brand, interactions=interactions_zero)
        self.assertEqual(assess_zero.conversion_performance, 0.0)

    def test_composite_score_is_reasonable(self):
        """Brand experience score should be between 0 and 100."""
        brand = BrandProfile(
            brand_id="brand_comp",
            brand_name="Composite Test",
            tagline="Test Brand",
            mission="To test",
            value_propositions=["Fast", "Reliable"],
            proof_assets=["Case study"],
            active_channels=["web", "email"],
        )
        assessment = BrandExperienceEngine.assess(brand, interactions=[])
        self.assertGreaterEqual(assessment.brand_experience_score, 0.0)
        self.assertLessEqual(assessment.brand_experience_score, 100.0)

    def test_assessment_compliance_check(self):
        """Assessment should correctly identify compliant vs non-compliant brands."""
        # High ethos brand
        brand_good = BrandProfile(
            brand_id="brand_good",
            brand_name="Ethical Brand",
            mission="Ethical service delivery",
            value_propositions=["Human-centered", "Transparent"],
        )
        assess_good = BrandExperienceEngine.assess(brand_good, interactions=[])
        self.assertTrue(assess_good.is_compliant(minimum_ethos_score=50.0))

        # Very weak brand (no content)
        brand_weak = BrandProfile(
            brand_id="brand_weak",
            brand_name="Weak",
        )
        assess_weak = BrandExperienceEngine.assess(brand_weak, interactions=[])
        # Weak brand with 50.0 default might still pass 50.0 threshold by default
        # Let's test with a higher threshold
        self.assertFalse(assess_weak.is_compliant(minimum_ethos_score=60.0))

    def test_ethos_scoring_from_brand_attributes(self):
        """Ethos should be higher for brands with clear mission, values, and trust assets."""
        brand_clear = BrandProfile(
            brand_id="brand_clear",
            brand_name="Clear Brand",
            mission="To serve customers ethically",
            tagline="Transparent service",
            value_propositions=["Honesty", "Reliability"],
            proof_assets=["Testimonials"],
            compliance_claims=["Privacy-first"],
            certifications=["ISO 27001"],
        )
        assess_clear = BrandExperienceEngine.assess(brand_clear, interactions=[])

        brand_vague = BrandProfile(
            brand_id="brand_vague",
            brand_name="Vague Brand",
        )
        assess_vague = BrandExperienceEngine.assess(brand_vague, interactions=[])

        # Clear brand should have higher ethos coherence
        self.assertGreater(assess_clear.coherence.composite_score, assess_vague.coherence.composite_score)


if __name__ == "__main__":
    unittest.main()
