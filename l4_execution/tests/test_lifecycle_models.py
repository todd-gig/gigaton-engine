"""Integration tests for lifecycle models: Campaign, RevenueEvent, CalibrationRecord."""

import unittest

from l4_execution.models.campaign import Campaign
from l4_execution.models.feedback_loop import CalibrationRecord, FeedbackStage
from l4_execution.models.revenue_event import RevenueEvent


class TestCampaignModel(unittest.TestCase):
    """Test Campaign lifecycle and operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.campaign = Campaign(
            campaign_id="camp_001",
            name="Q2 Email Nurture",
            channel="email",
            budget=5000.0,
        )

    def test_campaign_creation(self):
        """Test creating a campaign with defaults."""
        self.assertEqual(self.campaign.status, "draft")
        self.assertEqual(self.campaign.spend, 0.0)
        self.assertEqual(self.campaign.budget, 5000.0)

    def test_campaign_activate_from_draft(self):
        """Test activating a campaign from draft."""
        result = self.campaign.activate()
        self.assertTrue(result)
        self.assertEqual(self.campaign.status, "active")

    def test_campaign_activate_from_active_fails(self):
        """Test that activating an active campaign fails."""
        self.campaign.activate()
        result = self.campaign.activate()
        self.assertFalse(result)
        self.assertEqual(self.campaign.status, "active")

    def test_campaign_pause_from_active(self):
        """Test pausing an active campaign."""
        self.campaign.activate()
        result = self.campaign.pause()
        self.assertTrue(result)
        self.assertEqual(self.campaign.status, "paused")

    def test_campaign_pause_from_draft_fails(self):
        """Test that pausing a draft campaign fails."""
        result = self.campaign.pause()
        self.assertFalse(result)
        self.assertEqual(self.campaign.status, "draft")

    def test_campaign_resume_from_paused(self):
        """Test resuming a paused campaign."""
        self.campaign.activate()
        self.campaign.pause()
        result = self.campaign.resume()
        self.assertTrue(result)
        self.assertEqual(self.campaign.status, "active")

    def test_campaign_resume_from_draft_fails(self):
        """Test that resuming a draft campaign fails."""
        result = self.campaign.resume()
        self.assertFalse(result)
        self.assertEqual(self.campaign.status, "draft")

    def test_campaign_complete_from_active(self):
        """Test completing an active campaign."""
        self.campaign.activate()
        result = self.campaign.complete()
        self.assertTrue(result)
        self.assertEqual(self.campaign.status, "completed")

    def test_campaign_complete_from_paused(self):
        """Test completing a paused campaign."""
        self.campaign.activate()
        self.campaign.pause()
        result = self.campaign.complete()
        self.assertTrue(result)
        self.assertEqual(self.campaign.status, "completed")

    def test_campaign_complete_from_draft_fails(self):
        """Test that completing a draft campaign fails."""
        result = self.campaign.complete()
        self.assertFalse(result)
        self.assertEqual(self.campaign.status, "draft")

    def test_budget_remaining_calculation(self):
        """Test budget remaining calculation."""
        self.campaign.spend = 2000.0
        remaining = self.campaign.get_budget_remaining()
        self.assertEqual(remaining, 3000.0)

    def test_budget_remaining_when_over_budget(self):
        """Test budget remaining when spend exceeds budget."""
        self.campaign.spend = 6000.0
        remaining = self.campaign.get_budget_remaining()
        self.assertEqual(remaining, 0.0)  # Should not be negative

    def test_spend_rate_calculation(self):
        """Test spend rate calculation."""
        self.campaign.spend = 1000.0
        rate = self.campaign.get_spend_rate()
        self.assertEqual(rate, 20.0)  # 1000/5000 = 20%

    def test_spend_rate_at_budget(self):
        """Test spend rate when at budget."""
        self.campaign.spend = 5000.0
        rate = self.campaign.get_spend_rate()
        self.assertEqual(rate, 100.0)

    def test_spend_rate_zero_budget(self):
        """Test spend rate with zero budget."""
        zero_budget_campaign = Campaign(
            campaign_id="camp_002",
            name="Test",
            channel="email",
            budget=0.0,
        )
        rate = zero_budget_campaign.get_spend_rate()
        self.assertEqual(rate, 0.0)

    def test_campaign_with_leads(self):
        """Test adding leads to campaign."""
        self.campaign.lead_ids = ["lead_001", "lead_002", "lead_003"]
        self.assertEqual(len(self.campaign.lead_ids), 3)

    def test_campaign_with_interactions(self):
        """Test adding interactions to campaign."""
        self.campaign.interaction_ids = [
            "interact_001",
            "interact_002",
        ]
        self.assertEqual(len(self.campaign.interaction_ids), 2)


class TestRevenueEvent(unittest.TestCase):
    """Test RevenueEvent creation and validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.revenue = RevenueEvent(
            revenue_event_id="rev_001",
            lead_id="lead_001",
            amount=5000.0,
            revenue_type="new",
            confidence=0.85,
        )

    def test_revenue_event_creation(self):
        """Test creating a revenue event."""
        self.assertEqual(self.revenue.lead_id, "lead_001")
        self.assertEqual(self.revenue.amount, 5000.0)
        self.assertEqual(self.revenue.confidence, 0.85)

    def test_validate_positive_amount(self):
        """Test that positive amounts are valid."""
        self.assertTrue(self.revenue.validate_amount())

    def test_validate_zero_amount(self):
        """Test that zero amount is valid."""
        self.revenue.amount = 0.0
        self.assertTrue(self.revenue.validate_amount())

    def test_validate_negative_amount_invalid(self):
        """Test that negative amounts are invalid."""
        self.revenue.amount = -100.0
        self.assertFalse(self.revenue.validate_amount())

    def test_validate_confidence_at_bounds(self):
        """Test confidence at valid bounds."""
        self.revenue.confidence = 0.0
        self.assertTrue(self.revenue.validate_confidence())
        self.revenue.confidence = 1.0
        self.assertTrue(self.revenue.validate_confidence())

    def test_validate_confidence_in_range(self):
        """Test confidence in valid range."""
        self.revenue.confidence = 0.5
        self.assertTrue(self.revenue.validate_confidence())

    def test_validate_confidence_below_minimum(self):
        """Test confidence below minimum."""
        self.revenue.confidence = -0.1
        self.assertFalse(self.revenue.validate_confidence())

    def test_validate_confidence_above_maximum(self):
        """Test confidence above maximum."""
        self.revenue.confidence = 1.1
        self.assertFalse(self.revenue.validate_confidence())

    def test_adjust_confidence_increase(self):
        """Test increasing confidence."""
        initial = self.revenue.confidence
        result = self.revenue.adjust_confidence(0.1)
        self.assertTrue(result)
        self.assertEqual(self.revenue.confidence, initial + 0.1)

    def test_adjust_confidence_decrease(self):
        """Test decreasing confidence."""
        initial = self.revenue.confidence
        result = self.revenue.adjust_confidence(-0.1)
        self.assertTrue(result)
        self.assertEqual(self.revenue.confidence, initial - 0.1)

    def test_adjust_confidence_exceeds_upper_bound(self):
        """Test adjustment that would exceed upper bound fails."""
        self.revenue.confidence = 0.95
        result = self.revenue.adjust_confidence(0.1)
        self.assertFalse(result)
        self.assertEqual(self.revenue.confidence, 0.95)

    def test_adjust_confidence_exceeds_lower_bound(self):
        """Test adjustment that would exceed lower bound fails."""
        self.revenue.confidence = 0.05
        result = self.revenue.adjust_confidence(-0.1)
        self.assertFalse(result)
        self.assertEqual(self.revenue.confidence, 0.05)

    def test_revenue_with_attributions(self):
        """Test revenue with interaction attributions."""
        self.revenue.attribution_interactions = [
            "interact_001",
            "interact_002",
        ]
        self.assertEqual(len(self.revenue.attribution_interactions), 2)

    def test_revenue_type_variations(self):
        """Test different revenue types."""
        types = ["new", "expansion", "renewal", "retained"]
        for rev_type in types:
            revenue = RevenueEvent(
                revenue_event_id=f"rev_{rev_type}",
                lead_id="lead_001",
                amount=1000.0,
                revenue_type=rev_type,
            )
            self.assertEqual(revenue.revenue_type, rev_type)


class TestCalibrationRecord(unittest.TestCase):
    """Test CalibrationRecord and feedback loop logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.record = CalibrationRecord(
            record_id="cal_001",
            stage=FeedbackStage.COMPARE,
            metric_name="conversion_rate",
            predicted_value=0.25,
            realized_value=0.24,
            variance=-0.01,
            confidence_adjustment=0.05,
            timestamp="2026-04-21T12:00:00Z",
        )

    def test_calibration_record_creation(self):
        """Test creating a calibration record."""
        self.assertEqual(self.record.metric_name, "conversion_rate")
        self.assertEqual(self.record.stage, FeedbackStage.COMPARE)

    def test_calculate_variance(self):
        """Test variance calculation."""
        variance = self.record.calculate_variance()
        self.assertEqual(variance, self.record.predicted_value - self.record.realized_value)

    def test_validate_confidence_adjustment_at_bounds(self):
        """Test confidence adjustment at bounds."""
        self.record.confidence_adjustment = -1.0
        self.assertTrue(self.record.validate_confidence_adjustment())
        self.record.confidence_adjustment = 1.0
        self.assertTrue(self.record.validate_confidence_adjustment())

    def test_validate_confidence_adjustment_in_range(self):
        """Test confidence adjustment in range."""
        self.record.confidence_adjustment = 0.0
        self.assertTrue(self.record.validate_confidence_adjustment())

    def test_validate_confidence_adjustment_out_of_bounds(self):
        """Test confidence adjustment out of bounds."""
        self.record.confidence_adjustment = -1.1
        self.assertFalse(self.record.validate_confidence_adjustment())
        self.record.confidence_adjustment = 1.1
        self.assertFalse(self.record.validate_confidence_adjustment())

    def test_error_tolerance_met_within_3_percent(self):
        """Test error tolerance with 3% threshold."""
        # Predicted 100, Realized 100 = 0% error (well within 3%)
        self.record.predicted_value = 100.0
        self.record.realized_value = 100.0
        self.record.variance = self.record.calculate_variance()
        self.assertTrue(self.record.error_tolerance_met(3.0))

    def test_error_tolerance_exceeded(self):
        """Test error tolerance exceeded."""
        # Predicted 100, Realized 95 = 5% error, exceeds 3% threshold
        self.record.predicted_value = 100.0
        self.record.realized_value = 95.0
        self.record.variance = self.record.calculate_variance()
        self.assertFalse(self.record.error_tolerance_met(3.0))

    def test_error_tolerance_zero_predicted_value(self):
        """Test error tolerance when predicted is zero."""
        self.record.predicted_value = 0.0
        self.record.realized_value = 0.0
        self.record.variance = self.record.calculate_variance()
        self.assertTrue(self.record.error_tolerance_met(3.0))

    def test_error_tolerance_zero_predicted_nonzero_realized(self):
        """Test error tolerance when predicted is zero but realized is nonzero."""
        self.record.predicted_value = 0.0
        self.record.realized_value = 5.0
        self.record.variance = self.record.calculate_variance()
        self.assertFalse(self.record.error_tolerance_met(3.0))

    def test_feedback_stages(self):
        """Test all feedback loop stages."""
        stages = [
            FeedbackStage.OBSERVE,
            FeedbackStage.SCORE,
            FeedbackStage.ATTRIBUTE,
            FeedbackStage.COMPARE,
            FeedbackStage.ADJUST,
            FeedbackStage.UPDATE,
        ]
        for idx, stage in enumerate(stages):
            record = CalibrationRecord(
                record_id=f"cal_{idx}",
                stage=stage,
                metric_name=f"metric_{idx}",
                predicted_value=1.0,
                realized_value=1.0,
                variance=0.0,
                confidence_adjustment=0.0,
            )
            self.assertEqual(record.stage, stage)


if __name__ == "__main__":
    unittest.main()
