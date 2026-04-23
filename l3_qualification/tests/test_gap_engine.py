"""Tests for gap_engine.py — gap analysis and value leakage detection."""
import pytest
from l3_qualification.engines.gap_engine import (
    RTQLStage, EscalationLevel, LeakageRuleType,
    GapItem, ActionItem, LeakageAlert, LeakageReport,
    SystemScoreData, OVSResultData,
    CASCADE_MULTIPLIERS, SYSTEM_WEIGHTS, DEPENDENCY_CHAIN,
    gap_severity, trust_penalty_modifier, calculate_gap, calculate_priority,
    analyze_gaps, generate_action_items,
    ValueLeakageDetector,
)


class TestGapSeverityBands:
    """Test gap severity classification."""

    def test_critical_severity(self):
        """Verify critical severity at gap_score >= 46."""
        assert gap_severity(50.0) == "critical"
        assert gap_severity(46.0) == "critical"

    def test_major_severity(self):
        """Verify major severity at gap_score >= 26."""
        assert gap_severity(35.0) == "major"
        assert gap_severity(26.0) == "major"

    def test_moderate_severity(self):
        """Verify moderate severity at gap_score >= 11."""
        assert gap_severity(20.0) == "moderate"
        assert gap_severity(11.0) == "moderate"

    def test_minor_severity(self):
        """Verify minor severity at gap_score < 11."""
        assert gap_severity(10.0) == "minor"
        assert gap_severity(0.0) == "minor"


class TestTrustPenaltyModifier:
    """Test trust penalty calculation."""

    def test_noise_penalty(self):
        """Verify penalty for NOISE stage."""
        assert trust_penalty_modifier(RTQLStage.NOISE) == 1.25

    def test_weak_signal_penalty(self):
        """Verify penalty for WEAK_SIGNAL stage."""
        assert trust_penalty_modifier(RTQLStage.WEAK_SIGNAL) == 1.25

    def test_echo_signal_penalty(self):
        """Verify penalty for ECHO_SIGNAL stage."""
        assert trust_penalty_modifier(RTQLStage.ECHO_SIGNAL) == 1.25

    def test_qualified_penalty(self):
        """Verify penalty for QUALIFIED stage."""
        assert trust_penalty_modifier(RTQLStage.QUALIFIED) == 1.25

    def test_certification_gap_penalty(self):
        """Verify penalty for CERTIFICATION_GAP stage."""
        assert trust_penalty_modifier(RTQLStage.CERTIFICATION_GAP) == 1.10

    def test_certified_penalty(self):
        """Verify no penalty for CERTIFIED stage."""
        assert trust_penalty_modifier(RTQLStage.CERTIFIED) == 1.00


class TestCalculateGap:
    """Test gap calculation with trust penalty."""

    def test_no_gap_when_target_equals_actual(self):
        """Verify gap is zero when target == actual."""
        gap_score, penalty, severity = calculate_gap(
            actual=5.0,
            target=5.0,
            strategic_importance=1.0,
            rtql_stage=RTQLStage.CERTIFIED,
        )
        assert gap_score == 0.0
        assert severity == "minor"

    def test_gap_with_penalty(self):
        """Verify gap calculation applies trust penalty."""
        gap_score, penalty, severity = calculate_gap(
            actual=3.0,
            target=5.0,
            strategic_importance=1.0,
            rtql_stage=RTQLStage.NOISE,
        )
        # Gap = (5-3) × 1.0 × 1.25 = 2.5
        assert gap_score == 2.5
        assert penalty == 1.25

    def test_gap_without_penalty(self):
        """Verify gap calculation without penalty."""
        gap_score, penalty, severity = calculate_gap(
            actual=3.0,
            target=5.0,
            strategic_importance=1.0,
            rtql_stage=RTQLStage.CERTIFIED,
        )
        # Gap = (5-3) × 1.0 × 1.00 = 2.0
        assert gap_score == 2.0
        assert penalty == 1.00

    def test_gap_with_strategic_importance(self):
        """Verify strategic importance multiplier."""
        gap_score_low, _, _ = calculate_gap(
            actual=3.0,
            target=5.0,
            strategic_importance=0.5,
            rtql_stage=RTQLStage.CERTIFIED,
        )
        gap_score_high, _, _ = calculate_gap(
            actual=3.0,
            target=5.0,
            strategic_importance=2.0,
            rtql_stage=RTQLStage.CERTIFIED,
        )
        # Low importance: (5-3) × 0.5 × 1.0 = 1.0
        # High importance: (5-3) × 2.0 × 1.0 = 4.0
        assert gap_score_low == 1.0
        assert gap_score_high == 4.0

    def test_gap_severity_classification(self):
        """Verify gap severity is correctly classified."""
        _, _, sev_minor = calculate_gap(4.5, 5.0, 1.0, RTQLStage.CERTIFIED)
        # Minor: (5.0-4.5) × 1.0 × 1.0 = 0.5 < 11
        _, _, sev_major = calculate_gap(3.0, 5.0, 5.0, RTQLStage.NOISE)
        # Major: (5.0-3.0) × 5.0 × 1.25 = 12.5 >= 11 (but < 26, so "moderate")
        # For major (>= 26), need: (5.0-3.0) × 5.0 × 2.7 or higher
        # Let's use: (5.0-2.0) × 5.0 × 1.25 = 18.75 which is moderate, or increase strategic importance
        _, _, sev_critical = calculate_gap(1.0, 5.0, 10.0, RTQLStage.CERTIFIED)
        # Critical: (5.0-1.0) × 10.0 × 1.0 = 40.0 >= 46? No, so let's adjust
        _, _, sev_critical2 = calculate_gap(0.5, 5.0, 10.0, RTQLStage.CERTIFIED)
        # Critical: (5.0-0.5) × 10.0 × 1.0 = 45.0 which is still < 46, use different values
        _, _, sev_critical3 = calculate_gap(0.0, 5.0, 10.0, RTQLStage.CERTIFIED)
        # Critical: (5.0-0.0) × 10.0 × 1.0 = 50.0 >= 46
        assert sev_minor == "minor"
        assert sev_critical3 == "critical"


class TestCalculatePriority:
    """Test priority score calculation."""

    def test_priority_with_equal_weights(self):
        """Verify priority score is calculated correctly."""
        # Priority = (Gap×0.35) + (Leverage×0.30) + (Urgency×0.20) + (Value×0.15)
        # = (10×0.35) + (10×0.30) + (10×0.20) + (10×0.15)
        # = 3.5 + 3.0 + 2.0 + 1.5 = 10.0
        priority = calculate_priority(
            gap_score=10.0,
            leverage_score=10.0,
            urgency_score=10.0,
            value_matrix_impact=10.0,
        )
        assert priority == 10.0

    def test_priority_gap_dominates(self):
        """Verify gap score has highest weight (0.35)."""
        priority_high_gap = calculate_priority(
            gap_score=100.0,
            leverage_score=0.0,
            urgency_score=0.0,
            value_matrix_impact=0.0,
        )
        assert priority_high_gap == 35.0  # 100 × 0.35

    def test_priority_leverage_second(self):
        """Verify leverage has second-highest weight (0.30)."""
        priority_high_leverage = calculate_priority(
            gap_score=0.0,
            leverage_score=100.0,
            urgency_score=0.0,
            value_matrix_impact=0.0,
        )
        assert priority_high_leverage == 30.0  # 100 × 0.30

    def test_priority_zero_all_inputs(self):
        """Verify priority is 0 when all inputs are 0."""
        priority = calculate_priority(0.0, 0.0, 0.0, 0.0)
        assert priority == 0.0


class TestAnalyzeGaps:
    """Test batch gap analysis."""

    def test_analyze_single_gap(self):
        """Verify analysis of single gap."""
        items = [{
            "category": "Adoption",
            "variable": "Daily Active Users",
            "actual_score": 3.0,
            "target_score": 5.0,
            "strategic_importance": 1.0,
            "rtql_stage": "certified",
            "leverage_score": 5.0,
            "urgency_score": 4.0,
            "value_matrix_impact": 3.0,
        }]
        results = analyze_gaps(items)
        assert len(results) == 1
        assert isinstance(results[0], GapItem)
        assert results[0].gap_severity_label == "minor"

    def test_analyze_multiple_gaps_sorted_by_priority(self):
        """Verify multiple gaps sorted by priority descending."""
        items = [
            {
                "category": "A", "variable": "V1",
                "actual_score": 1.0, "target_score": 5.0,
                "strategic_importance": 1.0, "rtql_stage": "certified",
                "leverage_score": 1.0, "urgency_score": 1.0, "value_matrix_impact": 1.0,
            },
            {
                "category": "B", "variable": "V2",
                "actual_score": 1.0, "target_score": 5.0,
                "strategic_importance": 5.0, "rtql_stage": "certified",
                "leverage_score": 5.0, "urgency_score": 5.0, "value_matrix_impact": 5.0,
            },
        ]
        results = analyze_gaps(items)
        assert len(results) == 2
        # Second item should have higher priority due to higher strategic importance
        assert results[0].priority_score > results[1].priority_score

    def test_analyze_gaps_invalid_rtql_stage(self):
        """Verify invalid RTQL stage defaults to QUALIFIED."""
        items = [{
            "category": "A", "variable": "V1",
            "actual_score": 3.0, "target_score": 5.0,
            "strategic_importance": 1.0, "rtql_stage": "invalid_stage",
            "leverage_score": 1.0, "urgency_score": 1.0, "value_matrix_impact": 1.0,
        }]
        results = analyze_gaps(items)
        assert results[0].rtql_stage == RTQLStage.QUALIFIED

    def test_analyze_gaps_applies_trust_penalty(self):
        """Verify trust penalty is applied in batch analysis."""
        items = [{
            "category": "A", "variable": "V1",
            "actual_score": 3.0, "target_score": 5.0,
            "strategic_importance": 1.0, "rtql_stage": "noise",
            "leverage_score": 0.0, "urgency_score": 0.0, "value_matrix_impact": 0.0,
        }]
        results = analyze_gaps(items)
        # Gap = (5-3) × 1.0 × 1.25 = 2.5
        assert results[0].gap_score == 2.5
        assert results[0].trust_penalty == 1.25


class TestGenerateActionItems:
    """Test action item generation from gaps."""

    def test_generate_actions_minimum_moderate(self):
        """Verify only moderate+ severity gaps generate actions."""
        gaps = [
            GapItem(
                category="A", variable="V1", gap_score=5.0,
                gap_severity_label="minor", rtql_stage=RTQLStage.CERTIFIED,
            ),
            GapItem(
                category="B", variable="V2", gap_score=15.0,
                gap_severity_label="moderate", rtql_stage=RTQLStage.CERTIFIED,
            ),
        ]
        actions = generate_action_items(gaps, min_severity="moderate")
        # Only moderate and above should generate actions
        assert len(actions) == 1
        assert actions[0].variable == "V2"

    def test_generate_actions_noise_stage(self):
        """Verify research items for NOISE stage."""
        gaps = [
            GapItem(
                category="A", variable="V1", gap_score=15.0,
                gap_severity_label="moderate", rtql_stage=RTQLStage.NOISE,
            ),
        ]
        actions = generate_action_items(gaps, min_severity="moderate")
        assert len(actions) == 1
        action = actions[0]
        assert any("auditable" in r.lower() or "source" in r.lower() for r in action.required_research)

    def test_generate_actions_certification_gap_stage(self):
        """Verify research items for CERTIFICATION_GAP stage."""
        gaps = [
            GapItem(
                category="A", variable="V1", gap_score=15.0,
                gap_severity_label="moderate", rtql_stage=RTQLStage.CERTIFICATION_GAP,
            ),
        ]
        actions = generate_action_items(gaps, min_severity="moderate")
        assert len(actions) == 1
        action = actions[0]
        assert any("explainability" in r.lower() or "replication" in r.lower() for r in action.required_research)

    def test_generate_actions_all_severities(self):
        """Verify action generation for all severity levels."""
        gaps = [
            GapItem(category="A", variable="V1", gap_score=5.0, gap_severity_label="minor", rtql_stage=RTQLStage.CERTIFIED),
            GapItem(category="B", variable="V2", gap_score=15.0, gap_severity_label="moderate", rtql_stage=RTQLStage.CERTIFIED),
            GapItem(category="C", variable="V3", gap_score=35.0, gap_severity_label="major", rtql_stage=RTQLStage.CERTIFIED),
            GapItem(category="D", variable="V4", gap_score=50.0, gap_severity_label="critical", rtql_stage=RTQLStage.CERTIFIED),
        ]
        actions = generate_action_items(gaps, min_severity="minor")
        assert len(actions) == 4


class TestSystemWeights:
    """Test system weight constants."""

    def test_system_weights_values(self):
        """Verify SYSTEM_WEIGHTS mapping."""
        assert SYSTEM_WEIGHTS["People"] == 0.30
        assert SYSTEM_WEIGHTS["Process"] == 0.25
        assert SYSTEM_WEIGHTS["Technology"] == 0.25
        assert SYSTEM_WEIGHTS["Learning"] == 0.20

    def test_system_weights_sum(self):
        """Verify weights sum to 1.0."""
        total = sum(SYSTEM_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


class TestCascadeMultipliers:
    """Test cascade multiplier values."""

    def test_cascade_multipliers(self):
        """Verify CASCADE_MULTIPLIERS mapping."""
        assert CASCADE_MULTIPLIERS[1] == 1.0
        assert CASCADE_MULTIPLIERS[2] == 1.3
        assert CASCADE_MULTIPLIERS[3] == 1.7
        assert CASCADE_MULTIPLIERS[4] == 2.2


class TestValueLeakageDetector:
    """Test value leakage detection engine."""

    def test_detector_creation(self):
        """Verify ValueLeakageDetector instantiation."""
        detector = ValueLeakageDetector()
        assert detector.annual_org_value == 1_000_000.0
        assert detector.single_dim_threshold == 0.5
        assert detector.system_threshold == 0.6

    def test_detector_custom_parameters(self):
        """Verify custom parameter initialization."""
        detector = ValueLeakageDetector(
            annual_org_value=5_000_000.0,
            single_dim_threshold=0.4,
        )
        assert detector.annual_org_value == 5_000_000.0
        assert detector.single_dim_threshold == 0.4

    def test_detect_single_dimension_leakage(self):
        """Verify single-dimension leakage detection."""
        detector = ValueLeakageDetector()
        ovs = OVSResultData(
            people_score=SystemScoreData(
                name="People", score=0.7,
                dimensions={"dimension1": 0.3, "dimension2": 0.9}  # One below threshold
            ),
            process_score=SystemScoreData(name="Process", score=0.7),
            technology_score=SystemScoreData(name="Technology", score=0.7),
            learning_score=SystemScoreData(name="Learning", score=0.7),
        )
        report = detector.detect(ovs)
        assert any(a.rule_type == LeakageRuleType.SINGLE_DIMENSION for a in report.alerts)

    def test_detect_multi_cascade_leakage(self):
        """Verify multi-system cascade detection (2+ systems in leakage)."""
        detector = ValueLeakageDetector()
        ovs = OVSResultData(
            people_score=SystemScoreData(name="People", score=0.5, dimensions={}),  # Below threshold
            process_score=SystemScoreData(name="Process", score=0.5, dimensions={}),  # Below threshold
            technology_score=SystemScoreData(name="Technology", score=0.7, dimensions={}),
            learning_score=SystemScoreData(name="Learning", score=0.7, dimensions={}),
        )
        report = detector.detect(ovs)
        assert any(a.rule_type == LeakageRuleType.MULTI_CASCADE for a in report.alerts)
        # Should apply cascade multiplier for 2 systems
        assert report.cascade_multiplier_applied == CASCADE_MULTIPLIERS[2]

    def test_detect_trend_early_warning(self):
        """Verify trend-based early warning detection."""
        detector = ValueLeakageDetector()
        ovs = OVSResultData(
            people_score=SystemScoreData(
                name="People", score=0.7,
                dimensions={}, trend=-0.06  # Below threshold of -0.05
            ),
            process_score=SystemScoreData(name="Process", score=0.7, dimensions={}),
            technology_score=SystemScoreData(name="Technology", score=0.7, dimensions={}),
            learning_score=SystemScoreData(name="Learning", score=0.7, dimensions={}),
        )
        report = detector.detect(ovs)
        assert any(a.rule_type == LeakageRuleType.TREND_EARLY_WARNING for a in report.alerts)

    def test_detect_bottleneck(self):
        """Verify bottleneck detection (dependency chain blockage)."""
        detector = ValueLeakageDetector()
        ovs = OVSResultData(
            people_score=SystemScoreData(name="People", score=0.7, dimensions={}),  # Healthy
            process_score=SystemScoreData(name="Process", score=0.4, dimensions={}),  # Degraded (depends on People)
            technology_score=SystemScoreData(name="Technology", score=0.7, dimensions={}),
            learning_score=SystemScoreData(name="Learning", score=0.7, dimensions={}),
        )
        report = detector.detect(ovs)
        assert any(a.rule_type == LeakageRuleType.BOTTLENECK for a in report.alerts)

    def test_escalation_levels(self):
        """Verify escalation level assignment."""
        detector = ValueLeakageDetector()
        ovs = OVSResultData(
            people_score=SystemScoreData(
                name="People", score=0.7,
                dimensions={"dim1": 0.2}  # Critical severity
            ),
            process_score=SystemScoreData(name="Process", score=0.7, dimensions={}),
            technology_score=SystemScoreData(name="Technology", score=0.7, dimensions={}),
            learning_score=SystemScoreData(name="Learning", score=0.7, dimensions={}),
        )
        report = detector.detect(ovs)
        # Single dimension with very low score should be LEVEL_1_AUTOMATED
        critical_alerts = [a for a in report.alerts if a.severity == "critical"]
        assert any(a.escalation_level == EscalationLevel.LEVEL_1_AUTOMATED for a in critical_alerts)

    def test_total_estimated_loss(self):
        """Verify total estimated loss calculation."""
        detector = ValueLeakageDetector(annual_org_value=1_000_000.0)
        ovs = OVSResultData(
            people_score=SystemScoreData(
                name="People", score=0.7,
                dimensions={"engagement": 0.4},  # Below single_dim_threshold of 0.5
            ),
            process_score=SystemScoreData(name="Process", score=0.7, dimensions={}),
            technology_score=SystemScoreData(name="Technology", score=0.7, dimensions={}),
            learning_score=SystemScoreData(name="Learning", score=0.7, dimensions={}),
        )
        report = detector.detect(ovs)
        assert report.total_estimated_annual_loss >= 0.0
        assert len(report.alerts) >= 1

    def test_leakage_alert_severity_levels(self):
        """Verify alert severity is correctly set."""
        detector = ValueLeakageDetector()
        ovs = OVSResultData(
            people_score=SystemScoreData(
                name="People", score=0.7,
                dimensions={"dim1": 0.2, "dim2": 0.6}  # One critical, one warning
            ),
            process_score=SystemScoreData(name="Process", score=0.7, dimensions={}),
            technology_score=SystemScoreData(name="Technology", score=0.7, dimensions={}),
            learning_score=SystemScoreData(name="Learning", score=0.7, dimensions={}),
        )
        report = detector.detect(ovs)
        severities = [a.severity for a in report.alerts]
        assert "critical" in severities or "warning" in severities


class TestValueLeakageIntegration:
    """Integration tests for value leakage detection."""

    def test_complete_leakage_scenario(self):
        """Verify detection in complex multi-system scenario."""
        detector = ValueLeakageDetector(annual_org_value=10_000_000.0)
        ovs = OVSResultData(
            people_score=SystemScoreData(
                name="People", score=0.4, dimensions={"engagement": 0.3, "retention": 0.5}
            ),
            process_score=SystemScoreData(
                name="Process", score=0.45, dimensions={"efficiency": 0.4, "quality": 0.5}
            ),
            technology_score=SystemScoreData(
                name="Technology", score=0.8, dimensions={"availability": 0.85, "performance": 0.75}
            ),
            learning_score=SystemScoreData(
                name="Learning", score=0.7, dimensions={"adoption": 0.65, "effectiveness": 0.75},
                trend=-0.08  # Declining
            ),
        )
        report = detector.detect(ovs)

        # Should detect:
        # - Single dimension leakage (People engagement, Process efficiency, Learning trend)
        # - Multi-cascade (People + Process both below threshold)
        # - Bottleneck (People healthy but Process degrading)
        assert len(report.alerts) >= 3
        assert report.systems_in_leakage == 2  # People and Process
        assert report.cascade_multiplier_applied > 1.0
        assert report.total_estimated_annual_loss > 0.0
