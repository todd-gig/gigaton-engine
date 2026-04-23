"""BrandProfile dataclass for L2 Brand Experience module."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BrandProfile:
    """Core brand profile with identity, trust, and operational standards."""

    brand_id: str
    brand_name: str

    # Identity
    tagline: str = ""
    mission: str = ""
    value_propositions: List[str] = field(default_factory=list)
    differentiators: List[str] = field(default_factory=list)

    # Trust layer
    proof_assets: List[str] = field(default_factory=list)  # case studies, testimonials, etc.
    compliance_claims: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    # Channel presence
    active_channels: List[str] = field(default_factory=list)  # voice, sms, whatsapp, web, email, in_person

    # Standards
    target_response_time_seconds: float = 300.0  # 5 min target
    target_resolution_time_seconds: float = 3600.0  # 1 hour target
    target_conversion_rate: float = 0.15
    minimum_ethos_score: float = 50.0  # Below this = disqualifying
