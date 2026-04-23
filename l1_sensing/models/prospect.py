"""ProspectProfile dataclass for L1 Sensing module."""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class GTMMotion(str, Enum):
    """Go-to-market motion type."""
    PLG = "plg"
    SALES_LED = "sales_led"
    HYBRID = "hybrid"
    CHANNEL_LED = "channel_led"
    UNKNOWN = "unknown"


class PricingVisibility(str, Enum):
    """Pricing visibility type."""
    PUBLIC = "public"
    PARTIAL = "partial"
    CONTACT_SALES = "contact_sales"
    UNKNOWN = "unknown"


class MaturityLevel(str, Enum):
    """Capability maturity level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ADVANCED = "advanced"
    UNKNOWN = "unknown"


@dataclass
class CapabilitySummary:
    """Capability maturity summary for a prospect."""
    marketing_maturity: MaturityLevel = MaturityLevel.UNKNOWN
    sales_complexity: MaturityLevel = MaturityLevel.UNKNOWN
    measurement_maturity: MaturityLevel = MaturityLevel.UNKNOWN
    interaction_management_maturity: MaturityLevel = MaturityLevel.UNKNOWN


@dataclass
class ProspectProfile:
    """Core prospect profile with comprehensive business context."""
    prospect_id: str
    domain: str
    official_name: str
    industries: List[str] = field(default_factory=list)
    buyer_personas: List[str] = field(default_factory=list)
    service_geographies: List[str] = field(default_factory=list)
    gtm_motion: GTMMotion = GTMMotion.UNKNOWN
    pricing_visibility: PricingVisibility = PricingVisibility.UNKNOWN
    capability_summary: CapabilitySummary = field(default_factory=CapabilitySummary)
    last_verified_at: str = ""  # ISO 8601 format
    evidence_ids: List[str] = field(default_factory=list)
