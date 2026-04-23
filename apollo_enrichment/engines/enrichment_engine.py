"""EnrichmentEngine for enriching segments with Apollo data."""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# Ensure project root is in path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from segmentation.segment_library import SEGMENT_LIBRARY
from segmentation.engines.segmentation_engine import SegmentationEngine
from apollo_enrichment.models.enrichment_request import EnrichmentRequest, EnrichmentResult
from apollo_enrichment.models.enriched_lead import EnrichedLead
from apollo_enrichment.engines.apollo_client import ApolloClient


class EnrichmentEngine:
    """Enriches customer segments with Apollo API data."""

    def __init__(self, apollo_client: ApolloClient = None):
        """Initialize enrichment engine.

        Args:
            apollo_client: ApolloClient instance. Defaults to mock mode if None.
        """
        self.apollo_client = apollo_client or ApolloClient(mock_mode=True)
        self.segmentation_engine = SegmentationEngine(SEGMENT_LIBRARY)
        self._enrichment_history: Dict[str, EnrichmentResult] = {}

    def enrich_segment(self, segment_key: str, max_results: int = 25) -> Optional[EnrichmentResult]:
        """Enrich a segment with leads from Apollo.

        Args:
            segment_key: Key into SEGMENT_LIBRARY (e.g., "high_growth_low_infrastructure")
            max_results: Maximum leads to fetch per segment

        Returns:
            EnrichmentResult with enriched leads and metadata, or None if segment not found
        """
        # Look up segment
        if segment_key not in SEGMENT_LIBRARY:
            return None

        segment = SEGMENT_LIBRARY[segment_key]

        # Get Apollo filters from segment
        apollo_filters = segment.apollo_targeting.to_apollo_filters()

        # Create enrichment request
        request_id = self._generate_request_id()
        request = EnrichmentRequest(
            request_id=request_id,
            segment_id=segment.segment_id,
            segment_name=segment.segment_name,
            apollo_filters=apollo_filters,
            max_results=max_results,
            status="in_progress",
        )

        # Search Apollo for people matching filters
        raw_leads = self.apollo_client.search_people(apollo_filters, max_results)

        # Convert to EnrichedLead objects with segment context
        enriched_leads = []
        for raw_lead in raw_leads:
            enriched_lead = self._convert_to_enriched_lead(
                raw_lead, segment.segment_id, segment.segment_name
            )
            enriched_leads.append(enriched_lead)

        # Create result
        result = EnrichmentResult(
            request_id=request_id,
            segment_id=segment.segment_id,
            segment_name=segment.segment_name,
            leads=enriched_leads,
            total_found=len(enriched_leads),
            status="completed",
        )

        # Store in history
        self._enrichment_history[segment_key] = result

        return result

    def enrich_all_segments(self, max_per_segment: int = 10) -> Dict[str, EnrichmentResult]:
        """Enrich all segments in priority order.

        Args:
            max_per_segment: Max leads to fetch per segment

        Returns:
            Dict of segment_key -> EnrichmentResult
        """
        results = {}

        # Sort segments by priority_tier (1 first), then by expected value (highest first)
        sorted_segments = sorted(
            SEGMENT_LIBRARY.items(),
            key=lambda item: (
                item[1].priority_tier,
                -((item[1].expected_value_range[0] + item[1].expected_value_range[1]) / 2),
            ),
        )

        for segment_key, _ in sorted_segments:
            result = self.enrich_segment(segment_key, max_per_segment)
            if result:
                results[segment_key] = result

        return results

    def enrich_from_prospect(
        self,
        prospect,
        assessment,
        max_results: int = 25,
    ) -> Optional[EnrichmentResult]:
        """Classify a prospect and enrich its matched segment.

        Args:
            prospect: ProspectProfile instance
            assessment: ProspectValueAssessment instance
            max_results: Max leads to fetch for the matched segment

        Returns:
            EnrichmentResult for matched segment, or None if no segment match
        """
        # Use segmentation engine to classify prospect
        segment = self.segmentation_engine.classify_single(prospect, assessment)

        if not segment:
            return None

        # Find segment_key by matching segment_id
        segment_key = None
        for key, seg in SEGMENT_LIBRARY.items():
            if seg.segment_id == segment.segment_id:
                segment_key = key
                break

        if not segment_key:
            return None

        # Enrich the segment
        return self.enrich_segment(segment_key, max_results)

    def get_enrichment_summary(self) -> Dict[str, Any]:
        """Get summary of all enrichments run in this session.

        Returns:
            Dict with aggregated stats: total_leads, by_segment, enrichment_rates
        """
        total_leads = 0
        total_with_email = 0
        by_segment = {}

        for segment_key, result in self._enrichment_history.items():
            segment_info = {
                "segment_id": result.segment_id,
                "segment_name": result.segment_name,
                "total_leads": result.total_found,
                "leads_with_email": sum(1 for lead in result.leads if lead.email),
                "enrichment_rate": result.enrichment_rate,
                "request_id": result.request_id,
                "completed_at": result.completed_at,
            }
            by_segment[segment_key] = segment_info
            total_leads += result.total_found
            total_with_email += sum(1 for lead in result.leads if lead.email)

        overall_enrichment_rate = (
            (total_with_email / total_leads * 100) if total_leads > 0 else 0
        )

        return {
            "total_leads_enriched": total_leads,
            "total_leads_with_email": total_with_email,
            "overall_enrichment_rate": overall_enrichment_rate,
            "segments_enriched": len(by_segment),
            "by_segment": by_segment,
        }

    def _convert_to_enriched_lead(
        self, raw_lead: Dict[str, Any], segment_id: str, segment_name: str
    ) -> EnrichedLead:
        """Convert Apollo API response to EnrichedLead with segment context.

        Args:
            raw_lead: Dict from apollo_client.search_people()
            segment_id: Segment ID this lead matches
            segment_name: Segment name

        Returns:
            EnrichedLead with all fields populated
        """
        # Calculate fit score (0-100) based on how well lead matches segment
        # For now, use a simple heuristic: leads with more data get higher scores
        fit_score = 50.0  # baseline
        if raw_lead.get("email"):
            fit_score += 15
        if raw_lead.get("phone_number"):
            fit_score += 10
        if raw_lead.get("linkedin_url"):
            fit_score += 15
        if raw_lead.get("organization_domain"):
            fit_score += 10

        # Cap at 100
        fit_score = min(fit_score, 100.0)

        return EnrichedLead(
            lead_id=raw_lead.get("id", ""),
            segment_id=segment_id,
            segment_name=segment_name,
            first_name=raw_lead.get("first_name", ""),
            last_name=raw_lead.get("last_name", ""),
            title=raw_lead.get("title", ""),
            seniority=self._infer_seniority(raw_lead.get("title", "")),
            email=raw_lead.get("email", ""),
            phone=raw_lead.get("phone_number", ""),
            linkedin_url=raw_lead.get("linkedin_url", ""),
            company_name=raw_lead.get("organization_name", ""),
            company_domain=raw_lead.get("organization_domain", ""),
            company_industry=raw_lead.get("organization_industry", ""),
            company_size=raw_lead.get("organization_size", ""),
            company_revenue=raw_lead.get("organization_revenue_range", ""),
            fit_score=fit_score,
            enrichment_source="apollo",
        )

    def _infer_seniority(self, title: str) -> str:
        """Infer seniority level from job title.

        Args:
            title: Job title string

        Returns:
            One of: "c_suite", "vp", "director", "manager", "individual_contributor"
        """
        if not title:
            return "individual_contributor"

        title_lower = title.lower()

        if any(word in title_lower for word in ["ceo", "cfo", "cto", "coo", "cmo", "cro", "chief"]):
            return "c_suite"
        elif any(word in title_lower for word in ["vp", "vice president", "head of"]):
            return "vp"
        elif "director" in title_lower:
            return "director"
        elif "manager" in title_lower:
            return "manager"
        else:
            return "individual_contributor"

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        from datetime import datetime
        import random
        import string

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ENR-{timestamp}-{random_suffix}"
