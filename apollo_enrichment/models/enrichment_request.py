"""EnrichmentRequest and EnrichmentResult models for Apollo enrichment."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class EnrichmentRequest:
    """Request to enrich leads for a segment using Apollo API."""

    request_id: str
    segment_id: str
    segment_name: str
    apollo_filters: Dict[str, Any]  # from ApolloTargeting.to_apollo_filters()
    max_results: int = 25
    created_at: str = ""  # ISO timestamp
    status: str = "pending"  # pending, in_progress, completed, failed

    def __post_init__(self):
        """Set created_at timestamp if not provided."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class EnrichmentResult:
    """Result of Apollo enrichment for a segment."""

    request_id: str
    segment_id: str
    segment_name: str  # Human-readable segment name
    leads: List[Any]  # List of EnrichedLead objects
    total_found: int
    enrichment_rate: float = 0.0  # % of leads with email
    status: str = "completed"
    error_message: str = ""
    completed_at: str = ""  # ISO timestamp

    def __post_init__(self):
        """Calculate enrichment_rate and set completion timestamp."""
        if not self.completed_at:
            self.completed_at = datetime.utcnow().isoformat()

        # Calculate enrichment rate: percentage of leads with email
        if self.leads:
            leads_with_email = sum(1 for lead in self.leads if lead.email)
            self.enrichment_rate = (leads_with_email / len(self.leads)) * 100.0
        else:
            self.enrichment_rate = 0.0
