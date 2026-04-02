"""Core pricing engine — calculates prices across all supported models."""
from __future__ import annotations

from .models import CostInputs, PricingConfig, PricingResult, PricingType


class PricingEngine:
    """Stateless pricing calculator supporting fixed, tiered, subscription, and hybrid models."""

    def calculate(
        self,
        config: PricingConfig,
        costs: CostInputs,
        units: int = 1,
        discount_rate: float = 0.0,
    ) -> PricingResult:
        if config.pricing_type == PricingType.FIXED:
            return self._calculate_fixed(config, costs, discount_rate)
        elif config.pricing_type == PricingType.TIERED:
            return self._calculate_tiered(config, costs, units, discount_rate)
        elif config.pricing_type == PricingType.SUBSCRIPTION:
            return self._calculate_subscription(config, costs, discount_rate)
        elif config.pricing_type == PricingType.HYBRID:
            return self._calculate_hybrid(config, costs, units, discount_rate)
        else:
            raise ValueError(f"Unsupported pricing type: {config.pricing_type}")

    # ── Fixed ──────────────────────────────────────────────────────────

    def _calculate_fixed(
        self,
        config: PricingConfig,
        costs: CostInputs,
        discount_rate: float,
    ) -> PricingResult:
        base = config.base_price + config.setup_fee
        return self._finalize(base, costs, config, discount_rate)

    # ── Tiered ─────────────────────────────────────────────────────────

    def _calculate_tiered(
        self,
        config: PricingConfig,
        costs: CostInputs,
        units: int,
        discount_rate: float,
    ) -> PricingResult:
        if not config.tiers:
            raise ValueError("Tiered pricing requires at least one tier")

        unit_price = config.tiers[-1].unit_price  # default to last tier
        for tier in config.tiers:
            max_u = tier.max_units if tier.max_units is not None else float("inf")
            if tier.min_units <= units <= max_u:
                unit_price = tier.unit_price
                break

        base = (unit_price * units) + config.setup_fee
        return self._finalize(base, costs, config, discount_rate)

    # ── Subscription ───────────────────────────────────────────────────

    def _calculate_subscription(
        self,
        config: PricingConfig,
        costs: CostInputs,
        discount_rate: float,
    ) -> PricingResult:
        base = (
            config.setup_fee
            + config.recurring_fee * config.contract_term_months
        )
        return self._finalize(base, costs, config, discount_rate)

    # ── Hybrid (subscription base + per-unit variable) ─────────────────

    def _calculate_hybrid(
        self,
        config: PricingConfig,
        costs: CostInputs,
        units: int,
        discount_rate: float,
    ) -> PricingResult:
        base = (
            config.setup_fee
            + config.recurring_fee * config.contract_term_months
            + config.variable_fee_per_unit * units
        )
        return self._finalize(base, costs, config, discount_rate)

    # ── Shared finalization ────────────────────────────────────────────

    def _finalize(
        self,
        base_price: float,
        costs: CostInputs,
        config: PricingConfig,
        discount_rate: float,
    ) -> PricingResult:
        # Enforce max discount
        effective_discount = min(discount_rate, config.max_discount)

        discounted_price = base_price * (1 - effective_discount)
        discount_impact = base_price - discounted_price

        # Floor price: total cost / (1 - min margin)
        floor_price = (
            costs.total_cost / (1 - config.min_acceptable_margin)
            if config.min_acceptable_margin < 1.0
            else costs.total_cost
        )

        # Use the higher of discounted price or floor price
        recommended_price = max(discounted_price, floor_price)

        # Margins
        revenue = recommended_price
        gross_margin = (
            (revenue - costs.total_cost) / revenue if revenue > 0 else 0.0
        )
        contribution_margin = (
            (revenue - costs.variable_cost) / revenue if revenue > 0 else 0.0
        )

        # Warnings
        warnings: list[str] = []
        approval_required = False

        if discounted_price < floor_price:
            warnings.append(
                f"Discounted price ${discounted_price:.2f} is below floor ${floor_price:.2f}. "
                "Price raised to floor."
            )
            approval_required = True

        if gross_margin < config.min_acceptable_margin:
            warnings.append(
                f"Gross margin {gross_margin:.1%} is below minimum {config.min_acceptable_margin:.1%}."
            )
            approval_required = True

        if gross_margin < config.target_gross_margin:
            warnings.append(
                f"Gross margin {gross_margin:.1%} is below target {config.target_gross_margin:.1%}."
            )

        return PricingResult(
            recommended_price=round(recommended_price, 2),
            floor_price=round(floor_price, 2),
            gross_margin=round(gross_margin, 4),
            contribution_margin=round(contribution_margin, 4),
            discount_applied=round(effective_discount, 4),
            discount_impact=round(discount_impact, 2),
            margin_warnings=warnings,
            approval_required=approval_required,
        )
