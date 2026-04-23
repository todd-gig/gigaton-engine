"""
L3 Qualification — thin wrapper around the QBS Decision Engine.

The Decision Engine lives in claude_decision_logic_pack/ and provides:
  - ValueEngine (5-component weighted scoring)
  - TrustEngine (7-dimension trust scoring, 4 tiers)
  - RTQLEngine (7-stage sequential qualification)
  - CertEngine (QC→VC→TC→EC certificate chain)
  - VerdictEngine (auto_execute | escalate_tier_1 | escalate_tier_2 | block | needs_data)
  - PriorityEngine (composite priority score)

This module re-exports the engine so the pipeline can import from l3_qualification
without coupling to the external pack's directory structure.
"""
