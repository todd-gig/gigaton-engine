"""Tests for causal_engine.py — CausalMapper and supporting structures."""
import pytest
from l3_qualification.engines.causal_engine import (
    CausalLayer, CausalStrength, FailureCategory, PrecursorType, CausalMaturity,
    CausalLink, CausalChain, Attribution, FailureMode, PredictionAccuracy, CausalMapResult,
    LAYER_DAY_RANGES, ATTRIBUTION_WEIGHTS,
    CausalMapper,
)


class TestCausalLayerEnums:
    """Test layer and strength enumerations."""

    def test_causal_layer_values(self):
        """Verify CausalLayer enum values."""
        assert CausalLayer.PRIMARY.value == 1
        assert CausalLayer.SECONDARY.value == 2
        assert CausalLayer.TERTIARY.value == 3
        assert CausalLayer.COMPOUND.value == 4

    def test_layer_day_ranges(self):
        """Verify LAYER_DAY_RANGES mapping."""
        assert LAYER_DAY_RANGES[CausalLayer.PRIMARY] == (0, 7)
        assert LAYER_DAY_RANGES[CausalLayer.SECONDARY] == (7, 30)
        assert LAYER_DAY_RANGES[CausalLayer.TERTIARY] == (30, 90)
        assert LAYER_DAY_RANGES[CausalLayer.COMPOUND] == (90, 365)

    def test_causal_strength_weights(self):
        """Verify ATTRIBUTION_WEIGHTS mapping."""
        assert ATTRIBUTION_WEIGHTS[CausalStrength.PRIMARY] == 1.00
        assert ATTRIBUTION_WEIGHTS[CausalStrength.SECONDARY] == 0.70
        assert ATTRIBUTION_WEIGHTS[CausalStrength.TERTIARY] == 0.35
        assert ATTRIBUTION_WEIGHTS[CausalStrength.NONE] == 0.00


class TestCausalLink:
    """Test CausalLink dataclass."""

    def test_create_link_defaults(self):
        """Verify CausalLink creation with defaults."""
        link = CausalLink()
        assert link.link_id
        assert link.source_system == ""
        assert link.target_system == ""
        assert link.layer == CausalLayer.PRIMARY
        assert link.strength == CausalStrength.PRIMARY
        assert link.actual_value is None

    def test_create_link_with_values(self):
        """Verify CausalLink creation with explicit values."""
        link = CausalLink(
            decision_id="d1",
            source_system="System A",
            target_system="System B",
            layer=CausalLayer.SECONDARY,
            predicted_value=100.0,
            actual_value=75.0,
        )
        assert link.decision_id == "d1"
        assert link.source_system == "System A"
        assert link.target_system == "System B"
        assert link.layer == CausalLayer.SECONDARY
        assert link.predicted_value == 100.0
        assert link.actual_value == 75.0


class TestCausalChain:
    """Test CausalChain dataclass and methods."""

    def test_create_chain_defaults(self):
        """Verify CausalChain creation with defaults."""
        chain = CausalChain()
        assert chain.chain_id
        assert chain.decision_id == ""
        assert chain.links == []
        assert chain.total_predicted_value == 0.0
        assert chain.total_actual_value is None

    def test_links_at_layer(self):
        """Test filtering links by layer."""
        chain = CausalChain()
        chain.links = [
            CausalLink(layer=CausalLayer.PRIMARY, predicted_value=10.0),
            CausalLink(layer=CausalLayer.SECONDARY, predicted_value=20.0),
            CausalLink(layer=CausalLayer.PRIMARY, predicted_value=15.0),
        ]
        primary_links = chain.links_at_layer(CausalLayer.PRIMARY)
        assert len(primary_links) == 2
        assert sum(l.predicted_value for l in primary_links) == 25.0


class TestAttribution:
    """Test Attribution dataclass."""

    def test_total_attributed_property(self):
        """Verify total_attributed calculation."""
        attr = Attribution(
            outcome_name="Revenue",
            outcome_value=1000.0,
            attributions={"dec1": 500.0, "dec2": 300.0, "dec3": 200.0}
        )
        assert attr.total_attributed == 1000.0

    def test_total_attributed_empty(self):
        """Test total_attributed with empty attributions."""
        attr = Attribution(outcome_name="Revenue", outcome_value=1000.0)
        assert attr.total_attributed == 0.0


class TestFailureMode:
    """Test FailureMode dataclass."""

    def test_create_failure_mode(self):
        """Verify FailureMode creation."""
        mode = FailureMode(
            category=FailureCategory.EXECUTION,
            precursor=PrecursorType.MISALIGNMENT,
            affected_layer=CausalLayer.PRIMARY,
            description="Test failure",
        )
        assert mode.category == FailureCategory.EXECUTION
        assert mode.precursor == PrecursorType.MISALIGNMENT
        assert mode.detected is False


class TestPredictionAccuracy:
    """Test PredictionAccuracy dataclass."""

    def test_accuracy_calculation(self):
        """Verify accuracy property calculation."""
        acc = PredictionAccuracy(
            layer=CausalLayer.PRIMARY,
            predicted=100.0,
            actual=75.0,
        )
        assert acc.accuracy == 0.75

    def test_accuracy_zero_predicted(self):
        """Test accuracy with zero predicted."""
        acc = PredictionAccuracy(
            layer=CausalLayer.PRIMARY,
            predicted=0.0,
            actual=50.0,
        )
        assert acc.accuracy == 0.0

    def test_confidence_adjustment_high_accuracy(self):
        """Test confidence adjustment for high accuracy (>0.7)."""
        acc = PredictionAccuracy(
            layer=CausalLayer.PRIMARY,
            predicted=100.0,
            actual=80.0,  # 0.8 accuracy
        )
        assert acc.confidence_adjustment == 1.1

    def test_confidence_adjustment_low_accuracy(self):
        """Test confidence adjustment for low accuracy (<0.5)."""
        acc = PredictionAccuracy(
            layer=CausalLayer.PRIMARY,
            predicted=100.0,
            actual=40.0,  # 0.4 accuracy
        )
        assert acc.confidence_adjustment == 0.8

    def test_confidence_adjustment_medium_accuracy(self):
        """Test confidence adjustment for medium accuracy."""
        acc = PredictionAccuracy(
            layer=CausalLayer.PRIMARY,
            predicted=100.0,
            actual=60.0,  # 0.6 accuracy
        )
        assert acc.confidence_adjustment == 1.0


class TestCausalMapper:
    """Test CausalMapper engine."""

    def test_create_chain(self):
        """Verify chain creation and storage."""
        mapper = CausalMapper()
        links = [
            CausalLink(source_system="A", target_system="B", predicted_value=100.0),
            CausalLink(source_system="B", target_system="C", predicted_value=75.0),
        ]
        chain = mapper.create_chain("dec1", "Deploy Feature", links)

        assert chain.decision_id == "dec1"
        assert chain.decision_name == "Deploy Feature"
        assert len(chain.links) == 2
        assert all(link.decision_id == "dec1" for link in chain.links)
        assert chain.total_predicted_value == 175.0

    def test_record_outcome(self):
        """Verify outcome recording updates link data."""
        mapper = CausalMapper()
        link1 = CausalLink(source_system="A", target_system="B", predicted_value=100.0)
        link2 = CausalLink(source_system="B", target_system="C", predicted_value=75.0)
        chain = mapper.create_chain("dec1", "Test", [link1, link2])

        # Record outcome for first link
        updated_link = mapper.record_outcome(
            chain.chain_id, chain.links[0].link_id,
            "Positive engagement", 85.0
        )

        assert updated_link.actual_value == 85.0
        assert updated_link.actual_outcome == "Positive engagement"
        assert chain.total_actual_value == 85.0

    def test_record_outcome_multiple(self):
        """Verify chain total when multiple outcomes recorded."""
        mapper = CausalMapper()
        links = [
            CausalLink(source_system="A", target_system="B", predicted_value=100.0),
            CausalLink(source_system="B", target_system="C", predicted_value=75.0),
        ]
        chain = mapper.create_chain("dec1", "Test", links)

        mapper.record_outcome(chain.chain_id, chain.links[0].link_id, "Outcome 1", 85.0)
        mapper.record_outcome(chain.chain_id, chain.links[1].link_id, "Outcome 2", 60.0)

        assert chain.total_actual_value == 145.0

    def test_calculate_attribution(self):
        """Verify attribution calculation with strength weighting."""
        mapper = CausalMapper()

        # 2 contributing decisions: one primary (1.0), one secondary (0.7)
        # Total weight = 1.0 + 0.7 = 1.7
        # Outcome value = 100
        # Dec1 gets: 100 * (1.0/1.7) = 58.82
        # Dec2 gets: 100 * (0.7/1.7) = 41.18
        attr = mapper.calculate_attribution(
            outcome_name="Revenue",
            outcome_value=100.0,
            contributing_decisions=[
                ("dec1", CausalStrength.PRIMARY),
                ("dec2", CausalStrength.SECONDARY),
            ]
        )

        assert attr.outcome_name == "Revenue"
        assert attr.outcome_value == 100.0
        assert attr.total_attributed == 100.0
        assert "dec1" in attr.attributions
        assert "dec2" in attr.attributions
        # Verify weights: dec1 should have ~58.82, dec2 should have ~41.18
        assert abs(attr.attributions["dec1"] - 58.82) < 0.1
        assert abs(attr.attributions["dec2"] - 41.18) < 0.1

    def test_attribution_with_no_weight(self):
        """Verify attribution with NONE strength."""
        mapper = CausalMapper()
        attr = mapper.calculate_attribution(
            outcome_name="Test",
            outcome_value=100.0,
            contributing_decisions=[("dec1", CausalStrength.NONE)]
        )
        assert attr.total_attributed == 0.0

    def test_detect_execution_failure(self):
        """Verify execution failure detection (actual < 50% predicted)."""
        mapper = CausalMapper()
        link = CausalLink(
            source_system="A", target_system="B",
            predicted_value=100.0,
            actual_value=40.0,  # 40% accuracy
        )
        chain = mapper.create_chain("dec1", "Test", [link])

        modes = mapper.detect_failure_modes(chain)
        assert any(m.category == FailureCategory.EXECUTION for m in modes)

    def test_detect_assumption_failure(self):
        """Verify assumption failure detection (sign reversal)."""
        mapper = CausalMapper()
        link = CausalLink(
            source_system="A", target_system="B",
            predicted_value=100.0,
            actual_value=-50.0,  # Negative where positive expected
        )
        chain = mapper.create_chain("dec1", "Test", [link])

        modes = mapper.detect_failure_modes(chain)
        assert any(m.category == FailureCategory.ASSUMPTION for m in modes)

    def test_detect_emergence_failure(self):
        """Verify emergence failure detection (Layer 3 >50% deviation)."""
        mapper = CausalMapper()
        link = CausalLink(
            source_system="A", target_system="B",
            layer=CausalLayer.TERTIARY,
            predicted_value=100.0,
            actual_value=40.0,  # >50% deviation
        )
        chain = mapper.create_chain("dec1", "Test", [link])

        modes = mapper.detect_failure_modes(chain)
        assert any(m.category == FailureCategory.EMERGENCE for m in modes)

    def test_evaluate_predictions(self):
        """Verify prediction accuracy evaluation per layer."""
        mapper = CausalMapper()
        links = [
            CausalLink(layer=CausalLayer.PRIMARY, predicted_value=100.0, actual_value=80.0),
            CausalLink(layer=CausalLayer.PRIMARY, predicted_value=50.0, actual_value=45.0),
            CausalLink(layer=CausalLayer.SECONDARY, predicted_value=100.0, actual_value=70.0),
        ]
        chain = mapper.create_chain("dec1", "Test", links)

        accuracies = mapper.evaluate_predictions(chain)
        assert len(accuracies) == 2  # Two layers with data

        # PRIMARY: (80 + 45) / (100 + 50) = 125 / 150 = 0.833
        primary_acc = next(a for a in accuracies if a.layer == CausalLayer.PRIMARY)
        assert abs(primary_acc.accuracy - 0.833) < 0.01

    def test_assess_maturity_basic_tracking(self):
        """Verify maturity assessment at 60% accuracy."""
        mapper = CausalMapper()
        accuracies = [
            PredictionAccuracy(CausalLayer.PRIMARY, 100.0, 60.0),
        ]
        maturity = mapper.assess_maturity(accuracies)
        assert maturity == CausalMaturity.BASIC_TRACKING

    def test_assess_maturity_cascade_intelligence(self):
        """Verify maturity assessment at 75% accuracy."""
        mapper = CausalMapper()
        accuracies = [
            PredictionAccuracy(CausalLayer.PRIMARY, 100.0, 75.0),
        ]
        maturity = mapper.assess_maturity(accuracies)
        assert maturity == CausalMaturity.CASCADE_INTELLIGENCE

    def test_assess_maturity_adaptive_strategy(self):
        """Verify maturity assessment at 85% accuracy."""
        mapper = CausalMapper()
        accuracies = [
            PredictionAccuracy(CausalLayer.PRIMARY, 100.0, 85.0),
        ]
        maturity = mapper.assess_maturity(accuracies)
        assert maturity == CausalMaturity.ADAPTIVE_STRATEGY

    def test_assess_maturity_learning_integration(self):
        """Verify maturity assessment at 90%+ accuracy."""
        mapper = CausalMapper()
        accuracies = [
            PredictionAccuracy(CausalLayer.PRIMARY, 100.0, 92.0),
        ]
        maturity = mapper.assess_maturity(accuracies)
        assert maturity == CausalMaturity.LEARNING_INTEGRATION

    def test_full_analysis(self):
        """Verify full_analysis produces complete CausalMapResult."""
        mapper = CausalMapper()
        links = [
            CausalLink(
                source_system="A", target_system="B",
                predicted_value=100.0, actual_value=75.0,
            ),
        ]
        chain = mapper.create_chain("dec1", "Test", links)

        result = mapper.full_analysis(chain.chain_id)

        assert isinstance(result, CausalMapResult)
        assert result.chain == chain
        assert isinstance(result.failure_modes, list)
        assert isinstance(result.prediction_accuracies, list)
        assert isinstance(result.maturity, CausalMaturity)

    def test_record_outcome_nonexistent_chain(self):
        """Verify error on nonexistent chain."""
        mapper = CausalMapper()
        with pytest.raises(ValueError, match="Chain.*not found"):
            mapper.record_outcome("nonexistent", "link123", "outcome", 100.0)

    def test_full_analysis_nonexistent_chain(self):
        """Verify error on nonexistent chain in full_analysis."""
        mapper = CausalMapper()
        with pytest.raises(ValueError, match="Chain.*not found"):
            mapper.full_analysis("nonexistent")
