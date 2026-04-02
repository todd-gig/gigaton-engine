"""Margin optimizer — diagnoses profitability and ranks improvement levers."""
from __future__ import annotations

from .models import (
    AlertCondition,
    MarginLever,
    OptimizationResult,
    ProfitabilityRecord,
)


class MarginOptimizer:
    """Evaluates profitability across dimensions, runs alert rules, ranks levers."""

    def __init__(
        self,
        min_gross_margin: float = 0.20,
        target_gross_margin: float = 0.50,
        max_discount_rate: float = 0.30,
        max_support_cost_ratio: float = 0.15,
    ):
        self.min_gross_margin = min_gross_margin
        self.target_gross_margin = target_gross_margin
        self.max_discount_rate = max_discount_rate
        self.max_support_cost_ratio = max_support_cost_ratio

    def evaluate(
        self,
        records: list[ProfitabilityRecord],
        levers: list[MarginLever],
    ) -> OptimizationResult:
        # Sort records: worst margin first
        sorted_records = sorted(records, key=lambda r: r.gross_margin)

        # Run alert checks
        alerts = self._check_alerts(sorted_records)

        # Rank levers by priority score descending
        ranked = sorted(levers, key=lambda lv: lv.priority_score, reverse=True)

        # Expected total lift = sum of all lever lifts (optimistic ceiling)
        total_lift = sum(lv.estimated_margin_lift_pct for lv in ranked)

        return OptimizationResult(
            profitability=sorted_records,
            ranked_levers=ranked,
            alerts=alerts,
            expected_total_lift_pct=round(total_lift, 4),
        )

    def _check_alerts(
        self, records: list[ProfitabilityRecord]
    ) -> list[AlertCondition]:
        alerts: list[AlertCondition] = []
        for rec in records:
            # Gross margin below minimum
            if rec.gross_margin < self.min_gross_margin:
                alerts.append(
                    AlertCondition(
                        rule="gross_margin_below_minimum",
                        threshold=self.min_gross_margin,
                        actual=round(rec.gross_margin, 4),
                        triggered=True,
                        entity_name=rec.name,
                    )
                )
            # Gross margin below target (warning)
            elif rec.gross_margin < self.target_gross_margin:
                alerts.append(
                    AlertCondition(
                        rule="gross_margin_below_target",
                        threshold=self.target_gross_margin,
                        actual=round(rec.gross_margin, 4),
                        triggered=True,
                        entity_name=rec.name,
                    )
                )
            # Support cost ratio check
            if rec.revenue > 0:
                support_ratio = (rec.total_cost - rec.direct_cost) / rec.revenue
                if support_ratio > self.max_support_cost_ratio:
                    alerts.append(
                        AlertCondition(
                            rule="support_cost_exceeds_range",
                            threshold=self.max_support_cost_ratio,
                            actual=round(support_ratio, 4),
                            triggered=True,
                            entity_name=rec.name,
                        )
                    )
        return alerts
