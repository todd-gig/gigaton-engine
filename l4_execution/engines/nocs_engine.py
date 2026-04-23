"""Net Output Contribution Score (NOCS) engine."""

from dataclasses import dataclass

from l4_execution.models.action_benchmark import ActionBenchmark
from l4_execution.models.role_profile import RoleProfile


@dataclass
class NOCSResult:
    """Result of NOCS calculation."""

    raw_nocs: float
    confidence_factor: float
    final_nocs: float
    component_scores: dict
    role_id: str


class NOCSEngine:
    """Computes Net Output Contribution Score based on action benchmark and role profile."""

    @staticmethod
    def calculate(benchmark: ActionBenchmark, role: RoleProfile) -> NOCSResult:
        """
        Calculate NOCS from ActionBenchmark and RoleProfile.

        Formula:
            raw_nocs = sum(benchmark_dimension * role_weight for each dimension)
            final_nocs = raw_nocs * confidence_factor
            All scores bounded to [0, 100]

        Args:
            benchmark: ActionBenchmark with 12 dimension scores
            role: RoleProfile with 12 dimension weights

        Returns:
            NOCSResult with raw_nocs, confidence_factor, final_nocs, and component_scores
        """
        # Get all dimensions from benchmark
        benchmark_dims = benchmark.get_all_dimensions()

        # Calculate weighted contribution for each dimension
        component_scores = {}
        raw_nocs = 0.0

        for dimension, benchmark_value in benchmark_dims.items():
            weight = role.benchmark_weights.get(dimension, 0.0)
            weighted_contribution = benchmark_value * weight
            component_scores[dimension] = weighted_contribution
            raw_nocs += weighted_contribution

        # Bound raw_nocs to [0, 100]
        raw_nocs = max(0.0, min(100.0, raw_nocs))

        # Apply confidence factor
        confidence_factor = benchmark.confidence
        final_nocs = raw_nocs * confidence_factor

        # Bound final_nocs to [0, 100]
        final_nocs = max(0.0, min(100.0, final_nocs))

        return NOCSResult(
            raw_nocs=raw_nocs,
            confidence_factor=confidence_factor,
            final_nocs=final_nocs,
            component_scores=component_scores,
            role_id=role.role_id,
        )
