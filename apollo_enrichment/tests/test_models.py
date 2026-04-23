"""Tests for Apollo enrichment models."""

import pytest
from datetime import datetime
from apollo_enrichment.models.enrichment_request import EnrichmentRequest, EnrichmentResult
from apollo_enrichment.models.enriched_lead import EnrichedLead


class TestEnrichmentRequest:
    """Test EnrichmentRequest model."""

    def test_enrichment_request_creation(self):
        """Test creating an EnrichmentRequest."""
        filters = {"person_titles": ["VP Marketing"], "organization_industry_tag_ids": ["saas"]}
        request = EnrichmentRequest(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="High Growth",
            apollo_filters=filters,
            max_results=25,
        )

        assert request.request_id == "req-001"
        assert request.segment_id == "SEG_001"
        assert request.segment_name == "High Growth"
        assert request.apollo_filters == filters
        assert request.max_results == 25
        assert request.status == "pending"
        assert request.created_at  # Should be auto-set

    def test_enrichment_request_default_status(self):
        """Test that EnrichmentRequest defaults status to pending."""
        request = EnrichmentRequest(
            request_id="req-002",
            segment_id="SEG_002",
            segment_name="Enterprise",
            apollo_filters={},
        )
        assert request.status == "pending"

    def test_enrichment_request_created_at_auto_set(self):
        """Test that created_at is automatically set to ISO timestamp."""
        request = EnrichmentRequest(
            request_id="req-003",
            segment_id="SEG_003",
            segment_name="Test",
            apollo_filters={},
        )
        assert request.created_at
        # Should be ISO format
        datetime.fromisoformat(request.created_at)

    def test_enrichment_request_status_transitions(self):
        """Test that status can transition through valid states."""
        request = EnrichmentRequest(
            request_id="req-004",
            segment_id="SEG_004",
            segment_name="Test",
            apollo_filters={},
            status="pending",
        )

        request.status = "in_progress"
        assert request.status == "in_progress"

        request.status = "completed"
        assert request.status == "completed"

        request.status = "failed"
        assert request.status == "failed"


class TestEnrichmentResult:
    """Test EnrichmentResult model."""

    def test_enrichment_result_creation(self):
        """Test creating an EnrichmentResult."""
        lead1 = EnrichedLead(
            lead_id="lead-001",
            segment_id="SEG_001",
            first_name="Sarah",
            email="sarah@example.com",
        )
        lead2 = EnrichedLead(
            lead_id="lead-002",
            segment_id="SEG_001",
            first_name="Michael",
            email="michael@example.com",
        )

        result = EnrichmentResult(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="High Growth",
            leads=[lead1, lead2],
            total_found=2,
            status="completed",
        )

        assert result.request_id == "req-001"
        assert result.segment_id == "SEG_001"
        assert result.segment_name == "High Growth"
        assert len(result.leads) == 2
        assert result.total_found == 2
        assert result.status == "completed"

    def test_enrichment_result_enrichment_rate_calculation(self):
        """Test that enrichment_rate is calculated as percentage with email."""
        lead1 = EnrichedLead(lead_id="lead-001", segment_id="SEG_001", email="email@example.com")
        lead2 = EnrichedLead(lead_id="lead-002", segment_id="SEG_001", email="")
        lead3 = EnrichedLead(lead_id="lead-003", segment_id="SEG_001", email="email3@example.com")

        result = EnrichmentResult(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="Test",
            leads=[lead1, lead2, lead3],
            total_found=3,
        )

        # 2 out of 3 have email = 66.67%
        assert abs(result.enrichment_rate - 66.67) < 0.1

    def test_enrichment_result_enrichment_rate_all_with_email(self):
        """Test enrichment_rate when all leads have email."""
        leads = [
            EnrichedLead(lead_id=f"lead-{i:03d}", segment_id="SEG_001", email=f"email{i}@example.com")
            for i in range(5)
        ]

        result = EnrichmentResult(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="Test",
            leads=leads,
            total_found=5,
        )

        assert result.enrichment_rate == 100.0

    def test_enrichment_result_enrichment_rate_none_with_email(self):
        """Test enrichment_rate when no leads have email."""
        leads = [
            EnrichedLead(lead_id=f"lead-{i:03d}", segment_id="SEG_001", email="")
            for i in range(5)
        ]

        result = EnrichmentResult(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="Test",
            leads=leads,
            total_found=5,
        )

        assert result.enrichment_rate == 0.0

    def test_enrichment_result_enrichment_rate_empty_leads(self):
        """Test enrichment_rate with no leads."""
        result = EnrichmentResult(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="Test",
            leads=[],
            total_found=0,
        )

        assert result.enrichment_rate == 0.0

    def test_enrichment_result_completed_at_auto_set(self):
        """Test that completed_at is automatically set."""
        result = EnrichmentResult(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="Test",
            leads=[],
            total_found=0,
        )
        assert result.completed_at
        datetime.fromisoformat(result.completed_at)

    def test_enrichment_result_with_error(self):
        """Test EnrichmentResult with error state."""
        result = EnrichmentResult(
            request_id="req-001",
            segment_id="SEG_001",
            segment_name="Test",
            leads=[],
            total_found=0,
            status="failed",
            error_message="API rate limit exceeded",
        )

        assert result.status == "failed"
        assert result.error_message == "API rate limit exceeded"


class TestEnrichedLead:
    """Test EnrichedLead model."""

    def test_enriched_lead_creation(self):
        """Test creating an EnrichedLead."""
        lead = EnrichedLead(
            lead_id="lead-001",
            segment_id="SEG_001",
            segment_name="High Growth",
            first_name="Sarah",
            last_name="Smith",
            title="VP Marketing",
            email="sarah@example.com",
            company_name="TechCorp",
            company_domain="techcorp.com",
        )

        assert lead.lead_id == "lead-001"
        assert lead.first_name == "Sarah"
        assert lead.last_name == "Smith"
        assert lead.email == "sarah@example.com"
        assert lead.company_name == "TechCorp"

    def test_enriched_lead_has_email(self):
        """Test has_email() method."""
        lead_with_email = EnrichedLead(
            lead_id="lead-001", segment_id="SEG_001", email="test@example.com"
        )
        assert lead_with_email.has_email() is True

        lead_without_email = EnrichedLead(lead_id="lead-002", segment_id="SEG_001", email="")
        assert lead_without_email.has_email() is False

    def test_enriched_lead_full_name(self):
        """Test full_name() method."""
        lead = EnrichedLead(
            lead_id="lead-001",
            first_name="John",
            last_name="Doe",
            segment_id="SEG_001",
        )
        assert lead.full_name() == "John Doe"

    def test_enriched_lead_full_name_missing_first(self):
        """Test full_name() with missing first name."""
        lead = EnrichedLead(lead_id="lead-001", first_name="", last_name="Doe", segment_id="SEG_001")
        assert lead.full_name() == "Doe"

    def test_enriched_lead_full_name_missing_last(self):
        """Test full_name() with missing last name."""
        lead = EnrichedLead(lead_id="lead-001", first_name="John", last_name="", segment_id="SEG_001")
        assert lead.full_name() == "John"

    def test_enriched_lead_full_name_both_missing(self):
        """Test full_name() with both names missing."""
        lead = EnrichedLead(lead_id="lead-001", first_name="", last_name="", segment_id="SEG_001")
        assert lead.full_name() == ""

    def test_enriched_lead_enriched_at_auto_set(self):
        """Test that enriched_at is automatically set."""
        lead = EnrichedLead(lead_id="lead-001", segment_id="SEG_001")
        assert lead.enriched_at
        datetime.fromisoformat(lead.enriched_at)

    def test_enriched_lead_default_fit_score(self):
        """Test that fit_score defaults to 0.0."""
        lead = EnrichedLead(lead_id="lead-001", segment_id="SEG_001")
        assert lead.fit_score == 0.0

    def test_enriched_lead_default_enrichment_source(self):
        """Test that enrichment_source defaults to apollo."""
        lead = EnrichedLead(lead_id="lead-001", segment_id="SEG_001")
        assert lead.enrichment_source == "apollo"

    def test_enriched_lead_repr(self):
        """Test __repr__ method."""
        lead = EnrichedLead(
            lead_id="lead-001",
            segment_id="SEG_001",
            first_name="Sarah",
            last_name="Smith",
            company_name="TechCorp",
            email="sarah@example.com",
        )

        repr_str = repr(lead)
        assert "Sarah Smith" in repr_str
        assert "TechCorp" in repr_str
        assert "sarah@example.com" in repr_str

    def test_enriched_lead_repr_with_missing_email(self):
        """Test __repr__ when email is missing."""
        lead = EnrichedLead(
            lead_id="lead-001",
            segment_id="SEG_001",
            first_name="John",
            last_name="Doe",
            company_name="Company",
            email="",
        )

        repr_str = repr(lead)
        assert "no email" in repr_str
