"""EthosScorer for converting ethos dimensions to coherence scores and coefficients."""

from ..models.brand_coherence import BrandCoherenceScore


class EthosScorer:
    """Scores brand ethos alignment across 7 dimensions with weighted composite and coefficient."""

    # Dimension weights (must sum to 1.0)
    DIMENSION_WEIGHTS = {
        "truthfulness_explainability": 0.20,
        "human_centered_technology": 0.15,
        "long_term_value_creation": 0.18,
        "cost_roi_discipline": 0.12,
        "human_agency_respect": 0.10,
        "trust_contribution": 0.15,
        "manipulation_avoidance": 0.10,
    }

    @staticmethod
    def score(dimensions: dict) -> BrandCoherenceScore:
        """
        Calculate weighted composite score and derive coefficient from ethos dimensions.

        Args:
            dimensions: Dict with keys for each of the 7 ethos dimensions.
                       Expected keys: truthfulness_explainability, human_centered_technology,
                       long_term_value_creation, cost_roi_discipline, human_agency_respect,
                       trust_contribution, manipulation_avoidance

        Returns:
            BrandCoherenceScore with all dimensions, composite, and coefficient populated.

        Coefficient mapping (from 06_ethos_alignment_model.md):
            >= 90: 1.25
            >= 70: 1.0
            >= 50: 0.75
            < 50: 0.0
        """
        # Extract individual dimensions with defaults
        truth_exp = dimensions.get("truthfulness_explainability", 50.0)
        human_centered = dimensions.get("human_centered_technology", 50.0)
        long_term = dimensions.get("long_term_value_creation", 50.0)
        cost_roi = dimensions.get("cost_roi_discipline", 50.0)
        human_agency = dimensions.get("human_agency_respect", 50.0)
        trust = dimensions.get("trust_contribution", 50.0)
        manipulation = dimensions.get("manipulation_avoidance", 50.0)

        # Calculate weighted composite
        composite = (
            truth_exp * EthosScorer.DIMENSION_WEIGHTS["truthfulness_explainability"]
            + human_centered * EthosScorer.DIMENSION_WEIGHTS["human_centered_technology"]
            + long_term * EthosScorer.DIMENSION_WEIGHTS["long_term_value_creation"]
            + cost_roi * EthosScorer.DIMENSION_WEIGHTS["cost_roi_discipline"]
            + human_agency * EthosScorer.DIMENSION_WEIGHTS["human_agency_respect"]
            + trust * EthosScorer.DIMENSION_WEIGHTS["trust_contribution"]
            + manipulation * EthosScorer.DIMENSION_WEIGHTS["manipulation_avoidance"]
        )

        # Derive coefficient from composite score
        if composite >= 90.0:
            coefficient = 1.25
        elif composite >= 70.0:
            coefficient = 1.0
        elif composite >= 50.0:
            coefficient = 0.75
        else:
            coefficient = 0.0

        return BrandCoherenceScore(
            truthfulness_explainability=truth_exp,
            human_centered_technology=human_centered,
            long_term_value_creation=long_term,
            cost_roi_discipline=cost_roi,
            human_agency_respect=human_agency,
            trust_contribution=trust,
            manipulation_avoidance=manipulation,
            composite_score=composite,
            coefficient=coefficient,
        )
