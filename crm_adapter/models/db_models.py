"""Database schema definitions for CRM adapter.

Uses SQLite for development (zero-config, portable).
Schema is compatible with PostgreSQL for production upgrade.
DATABASE_URL env var controls the database path.
"""

# SQL schema for all CRM tables
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS prospects (
    prospect_id TEXT PRIMARY KEY,
    domain TEXT DEFAULT '',
    official_name TEXT DEFAULT '',
    industries TEXT DEFAULT '[]',
    buyer_personas TEXT DEFAULT '[]',
    service_geographies TEXT DEFAULT '[]',
    gtm_motion TEXT DEFAULT 'unknown',
    pricing_visibility TEXT DEFAULT 'unknown',
    marketing_maturity TEXT DEFAULT 'low',
    sales_complexity TEXT DEFAULT 'medium',
    measurement_maturity TEXT DEFAULT 'low',
    interaction_management_maturity TEXT DEFAULT 'low',
    last_verified_at TEXT DEFAULT '',
    evidence_ids TEXT DEFAULT '[]',
    -- L2 Brand Profile fields
    brand_id TEXT DEFAULT '',
    brand_name TEXT DEFAULT '',
    brand_tagline TEXT DEFAULT '',
    brand_mission TEXT DEFAULT '',
    brand_value_propositions TEXT DEFAULT '[]',
    brand_differentiators TEXT DEFAULT '[]',
    brand_proof_assets TEXT DEFAULT '[]',
    brand_compliance_claims TEXT DEFAULT '[]',
    brand_certifications TEXT DEFAULT '[]',
    brand_active_channels TEXT DEFAULT '["email","web"]',
    brand_target_response_time REAL DEFAULT 300.0,
    brand_target_resolution_time REAL DEFAULT 3600.0,
    brand_target_conversion_rate REAL DEFAULT 0.15,
    brand_minimum_ethos_score REAL DEFAULT 50.0,
    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS inferences (
    object_id TEXT PRIMARY KEY,
    prospect_id TEXT NOT NULL,
    inference_type TEXT DEFAULT 'pain_point',
    statement TEXT DEFAULT '',
    confidence REAL DEFAULT 0.5,
    evidence_ids TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (prospect_id) REFERENCES prospects(prospect_id)
);

CREATE TABLE IF NOT EXISTS interactions (
    interaction_id TEXT PRIMARY KEY,
    prospect_id TEXT NOT NULL,
    entity_id TEXT DEFAULT 'agent_01',
    channel TEXT DEFAULT 'email',
    timestamp TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'open',
    response_time_seconds REAL,
    resolution_time_seconds REAL,
    converted INTEGER DEFAULT 0,
    abandoned INTEGER DEFAULT 0,
    escalated INTEGER DEFAULT 0,
    sentiment_score REAL DEFAULT 0.5,
    trust_shift_score REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (prospect_id) REFERENCES prospects(prospect_id)
);

CREATE TABLE IF NOT EXISTS leads (
    lead_id TEXT PRIMARY KEY,
    prospect_id TEXT NOT NULL,
    entity_id TEXT DEFAULT '',
    status TEXT DEFAULT 'new',
    channel TEXT DEFAULT 'email',
    source TEXT DEFAULT '',
    score REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now')),
    qualified_at TEXT,
    converted_at TEXT,
    FOREIGN KEY (prospect_id) REFERENCES prospects(prospect_id)
);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    name TEXT DEFAULT '',
    channel TEXT DEFAULT 'email',
    status TEXT DEFAULT 'draft',
    start_date TEXT,
    end_date TEXT,
    target_segments TEXT DEFAULT '[]',
    lead_ids TEXT DEFAULT '[]',
    interaction_ids TEXT DEFAULT '[]',
    budget REAL DEFAULT 0.0,
    spend REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS revenue_events (
    revenue_event_id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    amount REAL DEFAULT 0.0,
    revenue_type TEXT DEFAULT 'new',
    attribution_interactions TEXT DEFAULT '[]',
    timestamp TEXT DEFAULT (datetime('now')),
    confidence REAL DEFAULT 0.5,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE TABLE IF NOT EXISTS pipeline_results (
    result_id TEXT PRIMARY KEY,
    prospect_id TEXT NOT NULL,
    run_at TEXT DEFAULT (datetime('now')),
    -- L1
    fit_score REAL DEFAULT 0.0,
    need_score REAL DEFAULT 0.0,
    service_fit_score REAL DEFAULT 0.0,
    readiness_score REAL DEFAULT 0.0,
    -- L2
    brand_experience_score REAL,
    brand_coherence_coefficient REAL,
    -- L3
    verdict TEXT DEFAULT '',
    value_score REAL DEFAULT 0.0,
    trust_score REAL DEFAULT 0.0,
    priority_score REAL DEFAULT 0.0,
    rtql_stage INTEGER DEFAULT 0,
    certificates TEXT DEFAULT '{}',
    blocking_gates TEXT DEFAULT '[]',
    -- L4
    interaction_count INTEGER DEFAULT 0,
    avg_nocs REAL DEFAULT 0.0,
    total_compensation REAL DEFAULT 0.0,
    -- Full result JSON
    full_result_json TEXT DEFAULT '{}',
    FOREIGN KEY (prospect_id) REFERENCES prospects(prospect_id)
);

CREATE TABLE IF NOT EXISTS silence_evaluations (
    eval_id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    evaluated_at TEXT DEFAULT (datetime('now')),
    priority_score REAL DEFAULT 0.0,
    selected_action TEXT DEFAULT 'do_not_execute',
    authority_level TEXT DEFAULT 'D1',
    policy_gate_result TEXT DEFAULT 'approved',
    executed INTEGER DEFAULT 0,
    executed_at TEXT,
    execution_result TEXT DEFAULT '',
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE TABLE IF NOT EXISTS segment_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prospect_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    segment_name TEXT DEFAULT '',
    priority_tier INTEGER DEFAULT 2,
    assigned_at TEXT DEFAULT (datetime('now')),
    brand_experience_score REAL,
    fit_score REAL,
    FOREIGN KEY (prospect_id) REFERENCES prospects(prospect_id)
);
"""
