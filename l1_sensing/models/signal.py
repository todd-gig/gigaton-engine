"""SignalRecord dataclass for L1 Sensing module."""

from dataclasses import dataclass, field
from typing import List, Any
from enum import Enum


class SignalClass(str, Enum):
    """Classification of signal type."""
    IDENTITY = "identity"
    AUDIENCE = "audience"
    NARRATIVE = "narrative"
    PRODUCT = "product"
    PRICING = "pricing"
    CONVERSION = "conversion"
    TRUST = "trust"
    TEAM = "team"
    TECHNICAL = "technical"
    SEO = "seo"
    INFRASTRUCTURE = "infrastructure"
    EXTERNAL = "external"


@dataclass
class SignalRecord:
    """Raw signal record from prospect intelligence gathering."""
    object_id: str
    prospect_id: str
    signal_class: SignalClass
    signal_subtype: str
    raw_value: Any
    normalized_value: Any
    source_url: str
    captured_at: str  # ISO 8601 format
    confidence: float  # 0-1
    evidence_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence is within bounds."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")

    @staticmethod
    def validate_signal_class(signal_class: str) -> bool:
        """Check if signal_class is valid."""
        valid_classes = {cls.value for cls in SignalClass}
        return signal_class in valid_classes
