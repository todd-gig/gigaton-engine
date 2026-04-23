"""Tests for learning_engine.py — outcome analysis and learning loops."""
import pytest
from l3_qualification.engines.learning_engine import (
    VarianceDirection, TrustRecommendation, UpdateTarget,
    OutcomeRecord, VarianceAnalysis, LearningRecord,
    VALUE_TOLERANCE_PCT, TIMELINE_TOLERANCE_DAYS,
    calculate_variance, LearningLoop, OutcomeReporter,
)


class TestVarianceEnums:
    """Test variance-related enumerations."""

    def test_variance_direction_values(self):
        """Verify VarianceDirection enum values."""
        assert VarianceDirection.POSITIVE.value == "positive"
        assert VarianceDirection.NEUTRAL.value == "neutral"
        assert VarianceDirection.NEGATIVE.value == "negative"

    def test_trust_recommendation_values(self):
        """Verify TrustRecommendation enum values."""
        assert TrustRecommendation.UPGRADE.value == "upgrade"
        assert TrustRecommendation.MAINTAIN.value == "maintain"
        assert TrustRecommendation.DOWNGRADE.value == "downgrade"
        assert TrustRecommendation.REVIEW.value == "review"

    def test_update_target_enum(self):
        """Verify UpdateTarget enum."""
        targets = list(UpdateTarget)
        assert len(targets) == 6


class TestConstants:
    """Test tolerance and threshold constants."""

    def test_value_tolerance_constant(self):
        """Verify VALUE_TOLERANCE_PCT."""
        assert VALUE_TOLERANCE_PCT == 0.10

    def test_timeline_tolerance_constant(self):
        """Verify TIMELINE_TOLERANCE_DAYS."""
        assert TIMELINE_TOLERANCE_DAYS == 3


class TestOutcomeRecord:
    """Test OutcomeRecord dataclass."""

    def test_create_outcome_record(self):
        """Verify OutcomeRecord creation."""
        record = OutcomeRecord(
            decision_id="d1",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=100.0,
            expected_timeline_days=7,
            expected_risk_level="low",
            actual_value=85.0,
            actual_timeline_days=7,
            actual_risk_materialized=False,
        )
        assert record.decision_id == "d1"
        assert record.expected_value == 100.0
        assert record.actual_value == 85.0


class TestVarianceAnalysis:
    """Test VarianceAnalysis dataclass."""

    def test_create_variance_analysis(self):
        """Verify VarianceAnalysis creation."""
        var = VarianceAnalysis(
            decision_id="d1",
            value_variance=-15.0,
            value_variance_pct=-0.15,
            value_direction=VarianceDirection.NEGATIVE,
            timeline_variance_days=0,
            timeline_direction=VarianceDirection.NEUTRAL,
        )
        assert var.decision_id == "d1"
        assert var.value_direction == VarianceDirection.NEGATIVE


class TestLearningRecord:
    """Test LearningRecord dataclass."""

    def test_create_learning_record(self):
        """Verify LearningRecord creation."""
        outcome = OutcomeRecord(decision_id="d1", expected_value=100.0, actual_value=85.0)
        variance = VarianceAnalysis(decision_id="d1", composite_variance_score=-0.15)
        record = LearningRecord(
            decision_id="d1",
            outcome=outcome,
            variance=variance,
        )
        assert record.decision_id == "d1"
        assert record.variance.composite_variance_score == -0.15


class TestCalculateVariance:
    """Test calculate_variance function."""

    def test_neutral_variance(self):
        """Verify variance when within tolerance."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=105.0,  # Within 10% tolerance
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = calculate_variance(outcome)
        assert variance.value_direction == VarianceDirection.NEUTRAL
        assert variance.timeline_direction == VarianceDirection.NEUTRAL

    def test_positive_variance(self):
        """Verify positive variance (actual > expected)."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=120.0,  # >10% above
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = calculate_variance(outcome)
        assert variance.value_direction == VarianceDirection.POSITIVE
        assert variance.value_variance > 0.0

    def test_negative_variance(self):
        """Verify negative variance (actual < expected)."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=75.0,  # <10% below
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = calculate_variance(outcome)
        assert variance.value_direction == VarianceDirection.NEGATIVE
        assert variance.value_variance < 0.0

    def test_variance_with_timeline_slippage(self):
        """Verify variance accounts for timeline deviation."""
        outcome1 = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=100.0,
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        outcome2 = OutcomeRecord(
            decision_id="d2",
            expected_value=100.0,
            actual_value=100.0,
            expected_timeline_days=7,
            actual_timeline_days=11,  # 4 days late (> TOLERANCE_DAYS=3)
        )
        variance1 = calculate_variance(outcome1)
        variance2 = calculate_variance(outcome2)
        # Both have perfect value but variance2 has timeline penalty
        assert variance2.timeline_direction == VarianceDirection.NEGATIVE
        assert variance2.composite_variance_score < variance1.composite_variance_score

    def test_trust_recommendation_upgrade(self):
        """Verify UPGRADE recommendation at high variance (>=0.5)."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=120.0,  # +20%
            expected_timeline_days=7,
            actual_timeline_days=6,
        )
        variance = calculate_variance(outcome)
        assert variance.trust_recommendation == TrustRecommendation.UPGRADE

    def test_trust_recommendation_maintain(self):
        """Verify MAINTAIN recommendation at moderate variance (>=-0.2)."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=95.0,  # -5% (within tolerance)
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = calculate_variance(outcome)
        assert variance.trust_recommendation == TrustRecommendation.MAINTAIN

    def test_trust_recommendation_review(self):
        """Verify REVIEW recommendation at low variance (>=-0.5)."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=60.0,  # -40%
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = calculate_variance(outcome)
        assert variance.trust_recommendation == TrustRecommendation.REVIEW

    def test_trust_recommendation_downgrade(self):
        """Verify DOWNGRADE recommendation at poor variance (<-0.5)."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=30.0,  # -70%
            expected_timeline_days=7,
            actual_timeline_days=15,  # Very late
        )
        variance = calculate_variance(outcome)
        assert variance.trust_recommendation == TrustRecommendation.DOWNGRADE

    def test_variance_zero_expected_value(self):
        """Verify variance handling when expected_value is 0."""
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=0.0,
            actual_value=50.0,
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        # Should not crash; behavior depends on implementation
        variance = calculate_variance(outcome)
        assert isinstance(variance, VarianceAnalysis)


class TestOutcomeReporter:
    """Test OutcomeReporter class."""

    def test_reporter_creation(self):
        """Verify OutcomeReporter instantiation."""
        reporter = OutcomeReporter()
        assert isinstance(reporter, OutcomeReporter)

    def test_record_outcome(self):
        """Verify record_outcome method."""
        reporter = OutcomeReporter()
        record = reporter.record_outcome(
            decision_id="d1",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=100.0,
            expected_timeline_days=7,
            expected_risk_level="low",
            actual_value=85.0,
            actual_timeline_days=7,
            actual_risk_materialized=False,
        )
        assert record is not None
        assert record.decision_id == "d1"

    def test_compare_expected_vs_actual(self):
        """Verify comparison of expected vs actual outcomes."""
        reporter = OutcomeReporter()
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=85.0,
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        comparison = reporter.compare_expected_vs_actual(outcome)
        assert comparison is not None
        assert comparison["expected_value"] == 100.0
        assert comparison["actual_value"] == 85.0

    def test_generate_outcome_summary(self):
        """Verify outcome summary generation."""
        reporter = OutcomeReporter()
        outcome = OutcomeRecord(
            decision_id="d1",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=100.0,
            actual_value=85.0,
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = VarianceAnalysis(decision_id="d1")
        record = LearningRecord(
            decision_id="d1",
            outcome=outcome,
            variance=variance,
        )
        summary = reporter.generate_outcome_summary(record)
        assert summary is not None
        assert "d1" in summary


class TestLearningLoop:
    """Test LearningLoop composite engine."""

    def test_learning_loop_creation(self):
        """Verify LearningLoop instantiation."""
        loop = LearningLoop()
        assert isinstance(loop, LearningLoop)

    def test_analyze_outcome(self):
        """Verify outcome analysis pipeline."""
        loop = LearningLoop()
        record = loop.analyze_outcome(
            decision_id="d1",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=100.0,
            expected_timeline_days=7,
            expected_risk_level="low",
            actual_value=85.0,
            actual_timeline_days=7,
            actual_risk_materialized=False,
        )
        assert record is not None
        assert record.decision_id == "d1"

    def test_compute_variance(self):
        """Verify variance computation."""
        loop = LearningLoop()
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=85.0,
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = loop.compute_variance(outcome)
        assert isinstance(variance, VarianceAnalysis)

    def test_recommend_trust_adjustment(self):
        """Verify trust recommendation."""
        loop = LearningLoop()
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=100.0,
            expected_timeline_days=7,
            actual_timeline_days=7,
        )
        variance = calculate_variance(outcome)
        record = LearningRecord(
            decision_id="d1",
            outcome=outcome,
            variance=variance,
        )
        recommendation = loop.recommend_trust_adjustment(record)
        assert isinstance(recommendation, TrustRecommendation)

    def test_generate_update_targets(self):
        """Verify update target derivation."""
        loop = LearningLoop()
        outcome = OutcomeRecord(
            decision_id="d1",
            expected_value=100.0,
            actual_value=75.0,
            expected_timeline_days=7,
            actual_timeline_days=10,
        )
        variance = calculate_variance(outcome)
        record = LearningRecord(
            decision_id="d1",
            outcome=outcome,
            variance=variance,
        )
        targets = loop.generate_update_targets(record)
        # Should return list of suggested update targets
        assert isinstance(targets, list)

    def test_compile_learning_report(self):
        """Verify learning report compilation."""
        loop = LearningLoop()
        record = loop.analyze_outcome(
            decision_id="d1",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=100.0,
            expected_timeline_days=7,
            expected_risk_level="low",
            actual_value=85.0,
            actual_timeline_days=7,
            actual_risk_materialized=False,
        )
        report = loop.compile_learning_report()
        assert isinstance(report, dict)
        assert "total_records" in report


class TestLearningLoopIntegration:
    """Integration tests for learning loop pipeline."""

    def test_full_outcome_to_recommendation_pipeline(self):
        """Verify complete outcome→variance→recommendation pipeline."""
        loop = LearningLoop()
        reporter = OutcomeReporter()

        # Create outcome record
        record = reporter.record_outcome(
            decision_id="d1",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=100.0,
            expected_timeline_days=7,
            expected_risk_level="low",
            actual_value=92.0,
            actual_timeline_days=7,
            actual_risk_materialized=False,
        )

        # Verify variance exists
        assert record.variance is not None

        # Get trust recommendation
        recommendation = loop.recommend_trust_adjustment(record)
        assert recommendation in list(TrustRecommendation)

        # Generate update targets
        targets = loop.generate_update_targets(record)
        assert isinstance(targets, list)

    def test_multiple_outcome_aggregation(self):
        """Verify handling of multiple outcomes for same decision class."""
        loop = LearningLoop()

        # Analyze multiple outcomes
        r1 = loop.analyze_outcome(
            decision_id="d1",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=100.0,
            expected_timeline_days=7,
            expected_risk_level="low",
            actual_value=95.0,
            actual_timeline_days=7,
            actual_risk_materialized=False,
        )
        r2 = loop.analyze_outcome(
            decision_id="d2",
            decision_class="feature_deployment",
            original_verdict="approved",
            expected_value=50.0,
            expected_timeline_days=7,
            expected_risk_level="low",
            actual_value=45.0,
            actual_timeline_days=7,
            actual_risk_materialized=False,
        )

        assert len(loop.records) == 2
        assert all(isinstance(r.variance, VarianceAnalysis) for r in loop.records)

        # Aggregate into learning report
        report = loop.compile_learning_report()
        assert report["total_records"] == 2
