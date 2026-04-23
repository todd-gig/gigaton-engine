"""EnrichedLead model for Apollo-enriched prospect data."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EnrichedLead:
    """A prospect enriched with Apollo API data, contextualized to a segment."""

    # Identifiers
    lead_id: str  # Apollo person_id or internal ID
    segment_id: str = ""
    segment_name: str = ""

    # Person fields
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    seniority: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""

    # Company fields
    company_name: str = ""
    company_domain: str = ""
    company_industry: str = ""
    company_size: str = ""  # e.g., "51-200", "201-500"
    company_revenue: str = ""  # e.g., "$10M-$50M"

    # Segmentation context
    fit_score: float = 0.0  # 0-100 based on how well this lead matches segment criteria
    enrichment_source: str = "apollo"
    enriched_at: str = ""  # ISO timestamp

    def __post_init__(self):
        """Set enriched_at timestamp if not provided."""
        if not self.enriched_at:
            self.enriched_at = datetime.utcnow().isoformat()

    def has_email(self) -> bool:
        """Check if lead has an email address."""
        return bool(self.email)

    def full_name(self) -> str:
        """Return full name or empty string if missing."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p).strip()

    def __repr__(self) -> str:
        """Return a concise string representation."""
        name = self.full_name() or "Unknown"
        company = self.company_name or "Unknown"
        email = f"({self.email})" if self.email else "(no email)"
        return f"EnrichedLead({name} at {company} {email})"
