# Gigaton Engine — Unified L1→L3→L4 Intelligence Stack

**TurtleIsland Solutions + Gigaton AI — April 2026**

> Brand + Interaction → Revenue → Predictable Profitability

## Architecture

```
L1 Sensing     → Prospect signal extraction, normalization, causal inference, value scoring
L3 Qualification → QBS Decision Engine (imported from claude_decision_logic_pack)
L4 Execution   → Interaction Matrix, NOCS scoring, compensation engine
```

## Quick Start

```bash
python -m pipeline.cli demo          # Full L1→L3→L4 pipeline demo
python -m pipeline.cli prospect      # Prospect analysis → decision → scoring
python -m pytest tests/ -v           # Full test suite
```

## Module Map

| Module | Layer | Purpose |
|--------|-------|---------|
| `l1_sensing/` | L1 | Prospect memory, signal taxonomy, causal inference, value scoring |
| `l3_qualification/` | L3 | Thin wrapper importing QBS Decision Engine |
| `l4_execution/` | L4 | Interaction matrix, 12-dim NOCS scoring, compensation engine |
| `pipeline/` | All | Orchestrator wiring L1→L3→L4, CLI, demo scenarios |
| `tests/` | All | Integration tests across layers |
