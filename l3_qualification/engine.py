"""
L3 Qualification Engine — wraps claude_decision_logic_pack.DecisionEngine.

Provides:
  - QualificationEngine.evaluate(decision_dict) → Decision (fully scored)
  - QualificationEngine.evaluate_raw(Decision) → Decision (pass-through to engine)

The `evaluate` method accepts a dict (from L1's decision bridge) and constructs
a Decision object, runs it through the full QBS pipeline, and returns the result.
"""
import sys
import os

# Add decision logic pack to path
_DECISION_PACK_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "claude_decision_logic_pack",
)
if _DECISION_PACK_DIR not in sys.path:
    sys.path.insert(0, _DECISION_PACK_DIR)

from decision_engine import DecisionEngine
from models.decision import Decision, DecisionVerdict, DecisionStatus


class QualificationEngine:
    """
    L3 Qualification Engine.

    Wraps the QBS Decision Engine to accept either:
      - A raw dict (from L1 prospect_to_decision bridge)
      - A Decision object directly

    Returns a fully scored Decision with verdict, certificates, and priority.
    """

    def __init__(self):
        self.engine = DecisionEngine()

    def evaluate(self, decision_dict: dict) -> Decision:
        """
        Evaluate a decision from a dict (L1 bridge output).

        Args:
            decision_dict: Dict with Decision field names and values.
                Required keys: decision_id, description
                Optional: all other Decision fields

        Returns:
            Fully scored Decision object
        """
        # Extract known fields, ignore extras
        known_fields = {
            "decision_id", "description", "reversibility", "blast_radius",
            "financial_exposure", "strategic_impact", "time_sensitivity",
            "source_reliability", "data_completeness", "corroboration",
            "recency", "chain_of_custody", "ethical_alignment", "consistency",
            "missing_variables",
        }
        filtered = {k: v for k, v in decision_dict.items() if k in known_fields}
        decision = Decision(**filtered)
        return self.engine.evaluate(decision)

    def evaluate_raw(self, decision: Decision) -> Decision:
        """
        Evaluate a pre-built Decision object directly.

        Args:
            decision: Decision object

        Returns:
            Fully scored Decision object
        """
        return self.engine.evaluate(decision)
