"""L2 Brand Experience Engine module for the Gigaton Engine.

Implements the Brand Experience Engine that measures brand coherence, ethos alignment,
channel consistency, and interaction quality performance.

Models:
    BrandProfile: Core brand identity, channels, and operational standards
    BrandCoherenceScore: 7 ethos dimensions with composite score and coefficient
    BrandExperienceAssessment: Comprehensive assessment across all dimensions

Engines:
    EthosScorer: Scores ethos dimensions and derives alignment coefficient
    BrandExperienceEngine: Main engine for comprehensive assessment
"""

from .models import BrandProfile, BrandCoherenceScore, BrandExperienceAssessment
from .engines import EthosScorer, BrandExperienceEngine

__all__ = [
    "BrandProfile",
    "BrandCoherenceScore",
    "BrandExperienceAssessment",
    "EthosScorer",
    "BrandExperienceEngine",
]
