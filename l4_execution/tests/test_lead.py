"""Unit tests for Lead model."""

import unittest

from l4_execution.models.lead import Lead, LeadStatus


class TestLeadTransitions(unittest.TestCase):
    """Test valid and invalid lead status transitions."""

    def setUp(self):
        """Set up test fixtures."""
        self.lead = Lead(
            lead_id="lead_001",
            prospect_id="prospect_001",
            entity_id="entity_001",
            status=LeadStatus.NEW,
        )

    def test_valid_new_to_working(self):
        """Test valid transition: new → working."""
        result = self.lead.transition(LeadStatus.WORKING)
        self.assertTrue(result)
        self.assertEqual(self.lead.status, LeadStatus.WORKING)

    def test_valid_working_to_nurturing(self):
        """Test valid transition: working → nurturing."""
        self.lead.transition(LeadStatus.WORKING)
        result = self.lead.transition(LeadStatus.NURTURING)
        self.assertTrue(result)
        self.assertEqual(self.lead.status, LeadStatus.NURTURING)

    def test_valid_nurturing_to_qualified(self):
        """Test valid transition: nurturing → qualified."""
        self.lead.transition(LeadStatus.WORKING)
        self.lead.transition(LeadStatus.NURTURING)
        result = self.lead.transition(LeadStatus.QUALIFIED)
        self.assertTrue(result)
        self.assertEqual(self.lead.status, LeadStatus.QUALIFIED)

    def test_valid_qualified_to_converted(self):
        """Test valid transition: qualified → converted."""
        self.lead.transition(LeadStatus.WORKING)
        self.lead.transition(LeadStatus.NURTURING)
        self.lead.transition(LeadStatus.QUALIFIED)
        result = self.lead.transition(LeadStatus.CONVERTED)
        self.assertTrue(result)
        self.assertEqual(self.lead.status, LeadStatus.CONVERTED)

    def test_valid_working_to_unqualified(self):
        """Test valid transition: working → unqualified."""
        self.lead.transition(LeadStatus.WORKING)
        result = self.lead.transition(LeadStatus.UNQUALIFIED)
        self.assertTrue(result)
        self.assertEqual(self.lead.status, LeadStatus.UNQUALIFIED)

    def test_valid_nurturing_to_unqualified(self):
        """Test valid transition: nurturing → unqualified."""
        self.lead.transition(LeadStatus.WORKING)
        self.lead.transition(LeadStatus.NURTURING)
        result = self.lead.transition(LeadStatus.UNQUALIFIED)
        self.assertTrue(result)
        self.assertEqual(self.lead.status, LeadStatus.UNQUALIFIED)

    def test_valid_qualified_to_unqualified(self):
        """Test valid transition: qualified → unqualified."""
        self.lead.transition(LeadStatus.WORKING)
        self.lead.transition(LeadStatus.NURTURING)
        self.lead.transition(LeadStatus.QUALIFIED)
        result = self.lead.transition(LeadStatus.UNQUALIFIED)
        self.assertTrue(result)
        self.assertEqual(self.lead.status, LeadStatus.UNQUALIFIED)

    def test_invalid_new_to_qualified(self):
        """Test invalid transition: new → qualified (should fail)."""
        result = self.lead.transition(LeadStatus.QUALIFIED)
        self.assertFalse(result)
        self.assertEqual(self.lead.status, LeadStatus.NEW)

    def test_invalid_new_to_converted(self):
        """Test invalid transition: new → converted (should fail)."""
        result = self.lead.transition(LeadStatus.CONVERTED)
        self.assertFalse(result)
        self.assertEqual(self.lead.status, LeadStatus.NEW)

    def test_invalid_converted_to_new(self):
        """Test invalid transition: converted → new (should fail)."""
        self.lead.transition(LeadStatus.WORKING)
        self.lead.transition(LeadStatus.NURTURING)
        self.lead.transition(LeadStatus.QUALIFIED)
        self.lead.transition(LeadStatus.CONVERTED)
        result = self.lead.transition(LeadStatus.NEW)
        self.assertFalse(result)
        self.assertEqual(self.lead.status, LeadStatus.CONVERTED)

    def test_invalid_unqualified_to_working(self):
        """Test invalid transition: unqualified → working (should fail)."""
        self.lead.transition(LeadStatus.WORKING)
        self.lead.transition(LeadStatus.UNQUALIFIED)
        result = self.lead.transition(LeadStatus.WORKING)
        self.assertFalse(result)
        self.assertEqual(self.lead.status, LeadStatus.UNQUALIFIED)


class TestLeadScoring(unittest.TestCase):
    """Test lead score validation and bounds."""

    def setUp(self):
        """Set up test fixtures."""
        self.lead = Lead(
            lead_id="lead_002",
            prospect_id="prospect_002",
            entity_id="entity_002",
            status=LeadStatus.NEW,
            score=50.0,
        )

    def test_score_at_minimum_valid(self):
        """Test score at minimum valid bound (0.0)."""
        self.lead.score = 0.0
        self.assertTrue(self.lead.validate_score())

    def test_score_at_maximum_valid(self):
        """Test score at maximum valid bound (100.0)."""
        self.lead.score = 100.0
        self.assertTrue(self.lead.validate_score())

    def test_score_in_middle_range(self):
        """Test score in middle of valid range."""
        self.lead.score = 50.0
        self.assertTrue(self.lead.validate_score())

    def test_score_below_minimum_invalid(self):
        """Test score below minimum (-0.1)."""
        self.lead.score = -0.1
        self.assertFalse(self.lead.validate_score())

    def test_score_above_maximum_invalid(self):
        """Test score above maximum (100.1)."""
        self.lead.score = 100.1
        self.assertFalse(self.lead.validate_score())

    def test_default_score_is_valid(self):
        """Test that default score is valid."""
        lead = Lead(
            lead_id="lead_003",
            prospect_id="prospect_003",
            entity_id="entity_003",
        )
        self.assertTrue(lead.validate_score())


class TestLeadInteractions(unittest.TestCase):
    """Test lead interaction tracking."""

    def setUp(self):
        """Set up test fixtures."""
        self.lead = Lead(
            lead_id="lead_004",
            prospect_id="prospect_004",
            entity_id="entity_004",
        )

    def test_default_interactions_empty(self):
        """Test that default interactions list is empty."""
        self.assertEqual(self.lead.interactions, [])

    def test_add_interaction(self):
        """Test adding an interaction."""
        self.lead.interactions.append("interaction_001")
        self.assertIn("interaction_001", self.lead.interactions)
        self.assertEqual(len(self.lead.interactions), 1)

    def test_multiple_interactions(self):
        """Test adding multiple interactions."""
        self.lead.interactions.extend(
            ["interaction_001", "interaction_002", "interaction_003"]
        )
        self.assertEqual(len(self.lead.interactions), 3)
        self.assertIn("interaction_002", self.lead.interactions)


class TestLeadAttributes(unittest.TestCase):
    """Test lead attribute initialization and access."""

    def test_lead_creation_with_defaults(self):
        """Test creating a lead with default values."""
        lead = Lead(
            lead_id="lead_005",
            prospect_id="prospect_005",
            entity_id="entity_005",
        )
        self.assertEqual(lead.status, LeadStatus.NEW)
        self.assertEqual(lead.channel, "")
        self.assertEqual(lead.source, "")
        self.assertEqual(lead.score, 0.0)
        self.assertEqual(lead.created_at, "")
        self.assertEqual(lead.qualified_at, "")
        self.assertEqual(lead.converted_at, "")

    def test_lead_creation_with_custom_values(self):
        """Test creating a lead with custom values."""
        lead = Lead(
            lead_id="lead_006",
            prospect_id="prospect_006",
            entity_id="entity_006",
            channel="email",
            source="inbound",
            score=75.5,
            created_at="2026-04-21T10:00:00Z",
        )
        self.assertEqual(lead.channel, "email")
        self.assertEqual(lead.source, "inbound")
        self.assertEqual(lead.score, 75.5)
        self.assertEqual(lead.created_at, "2026-04-21T10:00:00Z")


if __name__ == "__main__":
    unittest.main()
