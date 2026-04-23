"""RoleProfile model for role-specific benchmark weighting."""

from dataclasses import dataclass


# Default uniform weights across all 12 dimensions
DEFAULT_WEIGHTS = {
    "time_leverage": 0.08,
    "effort_intensity": 0.06,
    "output_quality": 0.12,
    "uniqueness": 0.07,
    "relational_capital": 0.08,
    "risk_reduction": 0.10,
    "probability_lift": 0.12,
    "multiplicative_effect": 0.10,
    "brand_adherence": 0.08,
    "interaction_effectiveness": 0.09,
    "economic_productivity": 0.06,
    "ethos_alignment": 0.04,
}

# Predefined role profiles
ROLE_PROFILES_DATA = {
    "sales_operator": {
        "time_leverage": 0.06,
        "effort_intensity": 0.04,
        "output_quality": 0.10,
        "uniqueness": 0.04,
        "relational_capital": 0.16,
        "risk_reduction": 0.08,
        "probability_lift": 0.14,
        "multiplicative_effect": 0.04,
        "brand_adherence": 0.06,
        "interaction_effectiveness": 0.16,
        "economic_productivity": 0.10,
        "ethos_alignment": 0.02,
    },
    "operations_manager": {
        "time_leverage": 0.12,
        "effort_intensity": 0.10,
        "output_quality": 0.14,
        "uniqueness": 0.04,
        "relational_capital": 0.04,
        "risk_reduction": 0.18,
        "probability_lift": 0.06,
        "multiplicative_effect": 0.04,
        "brand_adherence": 0.08,
        "interaction_effectiveness": 0.08,
        "economic_productivity": 0.10,
        "ethos_alignment": 0.02,
    },
    "automation_system_builder": {
        "time_leverage": 0.16,
        "effort_intensity": 0.06,
        "output_quality": 0.12,
        "uniqueness": 0.06,
        "relational_capital": 0.02,
        "risk_reduction": 0.10,
        "probability_lift": 0.10,
        "multiplicative_effect": 0.22,
        "brand_adherence": 0.02,
        "interaction_effectiveness": 0.04,
        "economic_productivity": 0.08,
        "ethos_alignment": 0.02,
    },
    "cx_marketing_operator": {
        "time_leverage": 0.06,
        "effort_intensity": 0.04,
        "output_quality": 0.10,
        "uniqueness": 0.03,
        "relational_capital": 0.14,
        "risk_reduction": 0.06,
        "probability_lift": 0.10,
        "multiplicative_effect": 0.04,
        "brand_adherence": 0.18,
        "interaction_effectiveness": 0.14,
        "economic_productivity": 0.06,
        "ethos_alignment": 0.05,
    },
    "founder_exec": {
        "time_leverage": 0.04,
        "effort_intensity": 0.02,
        "output_quality": 0.08,
        "uniqueness": 0.06,
        "relational_capital": 0.10,
        "risk_reduction": 0.16,
        "probability_lift": 0.16,
        "multiplicative_effect": 0.14,
        "brand_adherence": 0.06,
        "interaction_effectiveness": 0.04,
        "economic_productivity": 0.12,
        "ethos_alignment": 0.02,
    },
    "brand_manager": {
        "time_leverage": 0.04,
        "effort_intensity": 0.04,
        "output_quality": 0.14,
        "uniqueness": 0.06,
        "relational_capital": 0.08,
        "risk_reduction": 0.08,
        "probability_lift": 0.06,
        "multiplicative_effect": 0.04,
        "brand_adherence": 0.22,
        "interaction_effectiveness": 0.08,
        "economic_productivity": 0.04,
        "ethos_alignment": 0.12,
    },
    "analyst_forecaster": {
        "time_leverage": 0.08,
        "effort_intensity": 0.04,
        "output_quality": 0.16,
        "uniqueness": 0.06,
        "relational_capital": 0.02,
        "risk_reduction": 0.14,
        "probability_lift": 0.14,
        "multiplicative_effect": 0.10,
        "brand_adherence": 0.04,
        "interaction_effectiveness": 0.04,
        "economic_productivity": 0.14,
        "ethos_alignment": 0.04,
    },
}


@dataclass
class RoleProfile:
    """Defines a role and its benchmark dimension weights."""

    role_id: str
    role_name: str
    benchmark_weights: dict

    def validate_weights(self) -> bool:
        """Verify that weights sum to approximately 1.0."""
        total = sum(self.benchmark_weights.values())
        return 0.99 <= total <= 1.01

    @classmethod
    def create_default(cls, role_id: str, role_name: str) -> "RoleProfile":
        """Create a role profile with default weights."""
        return cls(role_id=role_id, role_name=role_name, benchmark_weights=DEFAULT_WEIGHTS.copy())

    @classmethod
    def create_predefined(cls, role_key: str) -> "RoleProfile":
        """Create a role profile from predefined templates."""
        if role_key not in ROLE_PROFILES_DATA:
            raise ValueError(f"Unknown role key: {role_key}")
        weights = ROLE_PROFILES_DATA[role_key]
        return cls(role_id=role_key, role_name=role_key.replace("_", " ").title(), benchmark_weights=weights)


# Convenience accessor for predefined roles
ROLE_PROFILES = {
    "sales_operator": RoleProfile.create_predefined("sales_operator"),
    "operations_manager": RoleProfile.create_predefined("operations_manager"),
    "automation_system_builder": RoleProfile.create_predefined("automation_system_builder"),
    "cx_marketing_operator": RoleProfile.create_predefined("cx_marketing_operator"),
    "founder_exec": RoleProfile.create_predefined("founder_exec"),
    "brand_manager": RoleProfile.create_predefined("brand_manager"),
    "analyst_forecaster": RoleProfile.create_predefined("analyst_forecaster"),
}
