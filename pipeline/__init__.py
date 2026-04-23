"""
Pipeline — L1→L3→L4 orchestrator for the Gigaton Engine.

Full flow:
  L1 Sensing     → ProspectValueEngine scores prospect, bridges to decision dict
  L3 Qualification → QualificationEngine evaluates decision (value, trust, RTQL, certs, verdict)
  L4 Execution   → InteractionScorer + NOCSEngine + CompensationEngine
"""
