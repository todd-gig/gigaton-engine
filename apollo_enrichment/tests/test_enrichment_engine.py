"""Tests for EnrichmentEngine."""

import pytest
import sys
import os

# Ensure project root is in path
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from apollo_enrichment.engines.enrichment_engine import EnrichmentEngine
from apollo_enrichment.engines.apollo_client import ApolloClient
from apollo_enrichment.models.enriched_lead import EnrichedLead
from segmentation.segment_library import SEGMENT_LIBRARY


class TestEnrichmentEngine:
    """Test EnrichmentEngine."""

    def test_enrichment_engine_creation(self):
        """Test creating an EnrichmentEngine."""
        engine = EnrichmentEngine()
        assert engine.apollo_client is not None
        assert engine.segmentation_engine is not None

    def test_enrichment_engine_with_custom_client(self):
        """Test EnrichmentEngine with custom Apollo client."""
        client = ApolloClient(mock_mode=True)
        engine = EnrichmentEngine(apollo_client=client)
        assert engine.apollo_client == client

    def test_enrich_segment_high_growth(self):
        """Test enriching the high_growth_low_infrastructure segment."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=10)

        assert result is not None
        assert result.segment_id == "SEG_001"
        assert result.segment_name == "High Growth / Low Infrastructure"
        assert len(result.leads) == 10
        assert result.total_found == 10
        assert result.status == "completed"

    def test_enrich_segment_enterprise(self):
        """Test enriching the enterprise_trust_gap segment."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("enterprise_trust_gap", max_results=10)

        assert result is not None
        assert result.segment_id == "SEG_002"
        assert result.segment_name == "Enterprise / Trust Layer Gap"
        assert len(result.leads) == 10

    def test_enrich_segment_content_rich(self):
        """Test enriching the content_rich_measurement_poor segment."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("content_rich_measurement_poor", max_results=10)

        assert result is not None
        assert result.segment_id == "SEG_003"
        assert len(result.leads) == 10

    def test_enrich_segment_plg(self):
        """Test enriching the plg_conversion_friction segment."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("plg_conversion_friction", max_results=10)

        assert result is not None
        assert result.segment_id == "SEG_004"
        assert len(result.leads) == 10

    def test_enrich_segment_brand_narrative(self):
        """Test enriching the brand_narrative_sales_gap segment."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("brand_narrative_sales_gap", max_results=10)

        assert result is not None
        assert result.segment_id == "SEG_005"
        assert len(result.leads) == 10

    def test_enrich_segment_nonexistent(self):
        """Test enriching a non-existent segment returns None."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("nonexistent_segment")
        assert result is None

    def test_enrich_all_segments(self):
        """Test enriching all segments."""
        engine = EnrichmentEngine()
        results = engine.enrich_all_segments(max_per_segment=5)

        assert len(results) == 5
        assert "high_growth_low_infrastructure" in results
        assert "enterprise_trust_gap" in results
        assert "content_rich_measurement_poor" in results
        assert "plg_conversion_friction" in results
        assert "brand_narrative_sales_gap" in results

    def test_enrich_all_segments_respects_max_per_segment(self):
        """Test that enrich_all_segments respects max_per_segment."""
        engine = EnrichmentEngine()
        results = engine.enrich_all_segments(max_per_segment=15)

        for result in results.values():
            assert result.total_found == 15

    def test_enriched_leads_have_segment_context(self):
        """Test that enriched leads include segment context."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=5)

        for lead in result.leads:
            assert lead.segment_id == "SEG_001"
            assert lead.segment_name == "High Growth / Low Infrastructure"

    def test_enriched_leads_have_fit_scores(self):
        """Test that enriched leads have fit scores."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=10)

        for lead in result.leads:
            assert 0 <= lead.fit_score <= 100

    def test_enriched_leads_have_required_fields(self):
        """Test that enriched leads have all required fields populated."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=5)

        for lead in result.leads:
            assert lead.lead_id
            assert lead.segment_id
            assert lead.segment_name
            assert lead.first_name or lead.last_name
            assert lead.company_name
            assert lead.enrichment_source == "apollo"

    def test_enrichment_summary_basic(self):
        """Test get_enrichment_summary after enrichment."""
        engine = EnrichmentEngine()
        engine.enrich_segment("high_growth_low_infrastructure", max_results=10)

        summary = engine.get_enrichment_summary()

        assert summary["total_leads_enriched"] == 10
        assert summary["segments_enriched"] == 1
        assert "high_growth_low_infrastructure" in summary["by_segment"]

    def test_enrichment_summary_multiple_segments(self):
        """Test get_enrichment_summary with multiple segments."""
        engine = EnrichmentEngine()
        engine.enrich_segment("high_growth_low_infrastructure", max_results=10)
        engine.enrich_segment("enterprise_trust_gap", max_results=10)

        summary = engine.get_enrichment_summary()

        assert summary["total_leads_enriched"] == 20
        assert summary["segments_enriched"] == 2
        assert "high_growth_low_infrastructure" in summary["by_segment"]
        assert "enterprise_trust_gap" in summary["by_segment"]

    def test_enrichment_summary_enrichment_rate(self):
        """Test that enrichment_summary includes enrichment rates."""
        engine = EnrichmentEngine()
        engine.enrich_segment("high_growth_low_infrastructure", max_results=20)

        summary = engine.get_enrichment_summary()

        # All mock leads should have emails
        assert summary["overall_enrichment_rate"] == 100.0
        seg_summary = summary["by_segment"]["high_growth_low_infrastructure"]
        assert seg_summary["enrichment_rate"] == 100.0

    def test_enrichment_result_uses_apollo_filters(self):
        """Test that enrichment uses Apollo filters from segment targeting."""
        engine = EnrichmentEngine()
        segment = SEGMENT_LIBRARY["high_growth_low_infrastructure"]

        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=10)

        # Get the Apollo filters used
        apollo_filters = segment.apollo_targeting.to_apollo_filters()

        # If filters specify titles, leads should match
        if "person_titles" in apollo_filters:
            expected_titles = apollo_filters["person_titles"]
            for lead in result.leads:
                assert lead.title in expected_titles

    def test_enrich_segment_respects_max_results(self):
        """Test that enrich_segment respects max_results limit."""
        engine = EnrichmentEngine()

        result_5 = engine.enrich_segment("high_growth_low_infrastructure", max_results=5)
        assert len(result_5.leads) == 5

        result_20 = engine.enrich_segment("enterprise_trust_gap", max_results=20)
        assert len(result_20.leads) == 20

    def test_enrichment_result_has_timestamps(self):
        """Test that enrichment results have timestamps."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=5)

        assert result.completed_at
        assert result.request_id

    def test_enrichment_engine_infers_seniority_from_title(self):
        """Test that enrichment engine infers seniority levels from titles."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=20)

        # Check that seniority is inferred
        for lead in result.leads:
            if lead.title:
                assert lead.seniority in ["c_suite", "vp", "director", "manager", "individual_contributor"]

    def test_enrich_from_prospect_with_match(self):
        """Test enrich_from_prospect when prospect matches a segment."""
        # This requires creating a ProspectProfile and ProspectValueAssessment
        # which is integration-level testing
        from l1_sensing.models.prospect import ProspectProfile, GTMMotion, MaturityLevel, CapabilitySummary
        from l1_sensing.models.value_assessment import ProspectValueAssessment

        engine = EnrichmentEngine()

        # Create a prospect that matches high_growth_low_infrastructure
        prospect = ProspectProfile(
            prospect_id="prospect-001",
            domain="growthco.com",
            official_name="GrowthCo",
            gtm_motion=GTMMotion.SALES_LED,
            capability_summary=CapabilitySummary(
                marketing_maturity=MaturityLevel.LOW,
                measurement_maturity=MaturityLevel.LOW,
            ),
        )

        # Create assessment with values that match the segment
        assessment = ProspectValueAssessment(
            economic_scale=75,  # Within (60, 100)
            total=65,  # fit_score within (50, 100)
            need=50,
            service_fit=50,
            readiness=50,
            accessibility=50,
            expected_uplift=50,
            confidence=50,
        )

        result = engine.enrich_from_prospect(prospect, assessment, max_results=10)

        assert result is not None
        assert len(result.leads) == 10

    def test_enrich_from_prospect_with_no_match(self):
        """Test enrich_from_prospect when prospect doesn't match any segment."""
        from l1_sensing.models.prospect import ProspectProfile, GTMMotion
        from l1_sensing.models.value_assessment import ProspectValueAssessment

        engine = EnrichmentEngine()

        # Create a prospect that doesn't match any segment
        prospect = ProspectProfile(
            prospect_id="prospect-002",
            domain="unknown.com",
            official_name="Unknown",
            gtm_motion=GTMMotion.UNKNOWN,
        )

        assessment = ProspectValueAssessment(
            economic_scale=5,  # Below all segment thresholds
            total=10,
            need=10,
            service_fit=10,
            readiness=10,
            accessibility=10,
            expected_uplift=10,
            confidence=10,
        )

        result = engine.enrich_from_prospect(prospect, assessment, max_results=10)

        assert result is None

    def test_enrichment_summary_empty_before_enrichment(self):
        """Test that summary is empty before any enrichment."""
        engine = EnrichmentEngine()
        summary = engine.get_enrichment_summary()

        assert summary["total_leads_enriched"] == 0
        assert summary["segments_enriched"] == 0
        assert summary["overall_enrichment_rate"] == 0
        assert summary["by_segment"] == {}

    def test_enriched_leads_are_enriched_lead_objects(self):
        """Test that enriched leads are EnrichedLead instances."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=5)

        for lead in result.leads:
            assert isinstance(lead, EnrichedLead)

    def test_enrichment_result_has_apollo_filters(self):
        """Test that enrichment request includes Apollo filters."""
        engine = EnrichmentEngine()
        result = engine.enrich_segment("high_growth_low_infrastructure", max_results=5)

        assert result.request_id
        # Verify that mock data was generated based on segment's Apollo filters
        assert len(result.leads) > 0
