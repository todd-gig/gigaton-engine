# L4 Execution Module

The L4 Execution module implements the Interaction Matrix and compensation engine for the Gigaton System. This module handles scoring actions, calculating Net Output Contribution Scores (NOCS), and computing compensation based on performance metrics.

## Directory Structure

```
l4_execution/
├── __init__.py
├── README.md (this file)
├── models/
│   ├── __init__.py
│   ├── interaction.py       # InteractionEvent dataclass
│   ├── action_benchmark.py  # ActionBenchmark with 12 dimensions
│   ├── role_profile.py      # RoleProfile with dimension weights
│   └── compensation.py      # CompensationEvent dataclass
├── engines/
│   ├── __init__.py
│   ├── nocs_engine.py              # NOCS calculation engine
│   ├── compensation_engine.py       # Compensation formula implementation
│   └── interaction_scorer.py        # InteractionEvent -> ActionBenchmark
└── tests/
    ├── __init__.py
    ├── test_nocs_engine.py          # 15 NOCS tests
    ├── test_compensation_engine.py  # 15 compensation tests
    └── test_interaction_scorer.py   # 14 interaction scoring tests
```

## Core Components

### Models

**InteractionEvent**: Represents a single brand interaction across any channel (voice, SMS, WhatsApp, web, email, in-person)
- Tracks response time, resolution time, conversion, abandonment, escalation
- Includes sentiment and trust shift scores

**ActionBenchmark**: 12-dimension scoring model for any action
- Dimensions: time_leverage, effort_intensity, output_quality, uniqueness, relational_capital, risk_reduction, probability_lift, multiplicative_effect, brand_adherence, interaction_effectiveness, economic_productivity, ethos_alignment
- All scores 0-100, with confidence factor 0-1

**RoleProfile**: Maps roles to dimension weights
- Predefined profiles: sales_operator, operations_manager, automation_system_builder
- Weights sum to ~1.0 for normalized calculation

**CompensationEvent**: Computed compensation breakdown
- Base + variable components
- Multipliers, coefficients, penalties tracked

### Engines

**NOCSEngine**: Calculates Net Output Contribution Score
- Multiplies benchmark scores by role weights
- Applies confidence factor
- Returns weighted component breakdown

**CompensationEngine**: Implements compensation formula
- Formula: C_i = B_i + (NSO_i * R * M_i * E_i) - P_i
- Ethos coefficient: 1.25 (>=90), 1.0 (>=70), 0.75 (>=50), 0.0 (<50)
- Configurable payout conversion rate ($/NOCS point)

**InteractionScorer**: Converts InteractionEvent to ActionBenchmark
- Heuristic scoring based on interaction metrics
- Time leverage from response speed
- Quality from conversion, abandonment, escalation
- Relational capital from sentiment and trust shift

## Test Suite

**49 total tests** across three test files:

- **test_nocs_engine.py** (15 tests): NOCS calculation validation
- **test_compensation_engine.py** (15 tests): Compensation formula and edge cases
- **test_interaction_scorer.py** (14 tests): Interaction-to-benchmark conversion

All tests pass. Run with:
```bash
python -m unittest discover -s l4_execution/tests -p "test_*.py" -v
```

## Usage Example

```python
from l4_execution.models.interaction import InteractionEvent
from l4_execution.engines.interaction_scorer import InteractionScorer
from l4_execution.engines.nocs_engine import NOCSEngine
from l4_execution.engines.compensation_engine import CompensationEngine
from l4_execution.models.role_profile import ROLE_PROFILES

# 1. Create interaction
interaction = InteractionEvent(
    interaction_id="int_123",
    entity_id="customer_456",
    channel="web",
    timestamp="2026-04-21T14:30:00Z",
    status="resolved",
    response_time_seconds=120,
    resolution_time_seconds=1800,
    converted=True,
    sentiment_score=0.85,
    trust_shift_score=0.3
)

# 2. Score interaction
benchmark = InteractionScorer.score(interaction, actor_id="rep_789")

# 3. Calculate NOCS for sales role
sales_role = ROLE_PROFILES["sales_operator"]
nocs_result = NOCSEngine.calculate(benchmark, sales_role)

# 4. Calculate compensation
comp_engine = CompensationEngine(payout_conversion_rate=50.0)
comp_event = comp_engine.calculate(
    base_amount=2000.0,
    nocs_result=nocs_result,
    strategic_multiplier=1.2,
    ethos_alignment_score=85.0,
    penalties=0.0
)

print(f"NOCS: {nocs_result.final_nocs:.1f}")
print(f"Total Compensation: ${comp_event.total_amount:.2f}")
```

## Design Principles

1. **Composability**: Each component is independently testable and reusable
2. **Bounded Values**: All scores kept within 0-100 range for consistency
3. **Transparency**: Component scores tracked for audit trail
4. **Fairness**: Ethos alignment prevents compensation for misaligned behavior
5. **Configurability**: Payout rates and multipliers adjustable per organization

## Dependencies

- Standard library only: dataclasses, typing, uuid
- No external dependencies required
