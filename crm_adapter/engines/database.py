"""Database engine — SQLite-backed storage for CRM data.

Reads DATABASE_URL from env (default: sqlite:///gigaton.db).
Provides CRUD operations for all CRM entities.
JSON serialization for list/dict fields stored as TEXT.
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from crm_adapter.models.db_models import SCHEMA_SQL


def _default_db_path() -> str:
    """Get database path from env or use default."""
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    return url if url else "gigaton.db"


class Database:
    """SQLite database engine for CRM data.

    Thread-safe via check_same_thread=False.
    Auto-creates schema on initialization.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. None = use DATABASE_URL env var.
                     ":memory:" for in-memory testing.
        """
        self.db_path = db_path or _default_db_path()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def _create_schema(self):
        """Create all tables if they don't exist."""
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

    # ── PROSPECTS ─────────────────────────────────────────────────

    def upsert_prospect(self, data: Dict[str, Any]) -> str:
        """Insert or update a prospect.

        Args:
            data: Dict with prospect fields. Must include 'prospect_id'.

        Returns:
            prospect_id
        """
        prospect_id = data.get("prospect_id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()

        # Serialize list fields
        for field in ["industries", "buyer_personas", "service_geographies",
                      "evidence_ids", "brand_value_propositions", "brand_differentiators",
                      "brand_proof_assets", "brand_compliance_claims", "brand_certifications",
                      "brand_active_channels"]:
            if field in data and isinstance(data[field], list):
                data[field] = json.dumps(data[field])

        self.conn.execute("""
            INSERT INTO prospects (
                prospect_id, domain, official_name, industries, buyer_personas,
                service_geographies, gtm_motion, pricing_visibility,
                marketing_maturity, sales_complexity, measurement_maturity,
                interaction_management_maturity, last_verified_at, evidence_ids,
                brand_id, brand_name, brand_tagline, brand_mission,
                brand_value_propositions, brand_differentiators, brand_proof_assets,
                brand_compliance_claims, brand_certifications, brand_active_channels,
                brand_target_response_time, brand_target_resolution_time,
                brand_target_conversion_rate, brand_minimum_ethos_score,
                created_at, updated_at
            ) VALUES (
                :prospect_id, :domain, :official_name, :industries, :buyer_personas,
                :service_geographies, :gtm_motion, :pricing_visibility,
                :marketing_maturity, :sales_complexity, :measurement_maturity,
                :interaction_management_maturity, :last_verified_at, :evidence_ids,
                :brand_id, :brand_name, :brand_tagline, :brand_mission,
                :brand_value_propositions, :brand_differentiators, :brand_proof_assets,
                :brand_compliance_claims, :brand_certifications, :brand_active_channels,
                :brand_target_response_time, :brand_target_resolution_time,
                :brand_target_conversion_rate, :brand_minimum_ethos_score,
                :created_at, :updated_at
            )
            ON CONFLICT(prospect_id) DO UPDATE SET
                domain=excluded.domain, official_name=excluded.official_name,
                industries=excluded.industries, buyer_personas=excluded.buyer_personas,
                gtm_motion=excluded.gtm_motion, pricing_visibility=excluded.pricing_visibility,
                marketing_maturity=excluded.marketing_maturity,
                sales_complexity=excluded.sales_complexity,
                measurement_maturity=excluded.measurement_maturity,
                interaction_management_maturity=excluded.interaction_management_maturity,
                brand_id=excluded.brand_id, brand_name=excluded.brand_name,
                brand_tagline=excluded.brand_tagline, brand_mission=excluded.brand_mission,
                brand_value_propositions=excluded.brand_value_propositions,
                brand_differentiators=excluded.brand_differentiators,
                brand_proof_assets=excluded.brand_proof_assets,
                updated_at=excluded.updated_at
        """, {
            "prospect_id": prospect_id,
            "domain": data.get("domain", ""),
            "official_name": data.get("official_name", ""),
            "industries": data.get("industries", "[]"),
            "buyer_personas": data.get("buyer_personas", "[]"),
            "service_geographies": data.get("service_geographies", "[]"),
            "gtm_motion": data.get("gtm_motion", "unknown"),
            "pricing_visibility": data.get("pricing_visibility", "unknown"),
            "marketing_maturity": data.get("marketing_maturity", "low"),
            "sales_complexity": data.get("sales_complexity", "medium"),
            "measurement_maturity": data.get("measurement_maturity", "low"),
            "interaction_management_maturity": data.get("interaction_management_maturity", "low"),
            "last_verified_at": data.get("last_verified_at", ""),
            "evidence_ids": data.get("evidence_ids", "[]"),
            "brand_id": data.get("brand_id", ""),
            "brand_name": data.get("brand_name", ""),
            "brand_tagline": data.get("brand_tagline", ""),
            "brand_mission": data.get("brand_mission", ""),
            "brand_value_propositions": data.get("brand_value_propositions", "[]"),
            "brand_differentiators": data.get("brand_differentiators", "[]"),
            "brand_proof_assets": data.get("brand_proof_assets", "[]"),
            "brand_compliance_claims": data.get("brand_compliance_claims", "[]"),
            "brand_certifications": data.get("brand_certifications", "[]"),
            "brand_active_channels": data.get("brand_active_channels", '["email","web"]'),
            "brand_target_response_time": data.get("brand_target_response_time", 300.0),
            "brand_target_resolution_time": data.get("brand_target_resolution_time", 3600.0),
            "brand_target_conversion_rate": data.get("brand_target_conversion_rate", 0.15),
            "brand_minimum_ethos_score": data.get("brand_minimum_ethos_score", 50.0),
            "created_at": now,
            "updated_at": now,
        })
        self.conn.commit()
        return prospect_id

    def get_prospect(self, prospect_id: str) -> Optional[Dict[str, Any]]:
        """Get a prospect by ID."""
        row = self.conn.execute(
            "SELECT * FROM prospects WHERE prospect_id = ?", (prospect_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def list_prospects(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all prospects."""
        rows = self.conn.execute(
            "SELECT * FROM prospects ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── INTERACTIONS ──────────────────────────────────────────────

    def add_interaction(self, data: Dict[str, Any]) -> str:
        """Add an interaction event."""
        interaction_id = data.get("interaction_id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()

        self.conn.execute("""
            INSERT INTO interactions (
                interaction_id, prospect_id, entity_id, channel, timestamp,
                status, response_time_seconds, resolution_time_seconds,
                converted, abandoned, escalated, sentiment_score, trust_shift_score,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction_id,
            data.get("prospect_id", ""),
            data.get("entity_id", "agent_01"),
            data.get("channel", "email"),
            data.get("timestamp", now),
            data.get("status", "open"),
            data.get("response_time_seconds"),
            data.get("resolution_time_seconds"),
            1 if data.get("converted") else 0,
            1 if data.get("abandoned") else 0,
            1 if data.get("escalated") else 0,
            data.get("sentiment_score", 0.5),
            data.get("trust_shift_score", 0.0),
            now,
        ))
        self.conn.commit()
        return interaction_id

    def get_interactions(self, prospect_id: str) -> List[Dict[str, Any]]:
        """Get all interactions for a prospect."""
        rows = self.conn.execute(
            "SELECT * FROM interactions WHERE prospect_id = ? ORDER BY timestamp DESC",
            (prospect_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── LEADS ─────────────────────────────────────────────────────

    def upsert_lead(self, data: Dict[str, Any]) -> str:
        """Insert or update a lead."""
        lead_id = data.get("lead_id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()

        self.conn.execute("""
            INSERT INTO leads (
                lead_id, prospect_id, entity_id, status, channel, source,
                score, created_at, qualified_at, converted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(lead_id) DO UPDATE SET
                status=excluded.status, score=excluded.score,
                qualified_at=excluded.qualified_at, converted_at=excluded.converted_at
        """, (
            lead_id,
            data.get("prospect_id", ""),
            data.get("entity_id", ""),
            data.get("status", "new"),
            data.get("channel", "email"),
            data.get("source", ""),
            data.get("score", 0.0),
            now,
            data.get("qualified_at"),
            data.get("converted_at"),
        ))
        self.conn.commit()
        return lead_id

    def get_leads(self, prospect_id: str) -> List[Dict[str, Any]]:
        """Get all leads for a prospect."""
        rows = self.conn.execute(
            "SELECT * FROM leads WHERE prospect_id = ? ORDER BY created_at DESC",
            (prospect_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── PIPELINE RESULTS ──────────────────────────────────────────

    def store_pipeline_result(self, prospect_id: str, result_data: Dict[str, Any]) -> str:
        """Store a pipeline result."""
        result_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        self.conn.execute("""
            INSERT INTO pipeline_results (
                result_id, prospect_id, run_at, fit_score, need_score,
                service_fit_score, readiness_score, brand_experience_score,
                brand_coherence_coefficient, verdict, value_score, trust_score,
                priority_score, rtql_stage, certificates, blocking_gates,
                interaction_count, avg_nocs, total_compensation, full_result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id, prospect_id, now,
            result_data.get("fit_score", 0),
            result_data.get("need_score", 0),
            result_data.get("service_fit_score", 0),
            result_data.get("readiness_score", 0),
            result_data.get("brand_experience_score"),
            result_data.get("brand_coherence_coefficient"),
            result_data.get("verdict", ""),
            result_data.get("value_score", 0),
            result_data.get("trust_score", 0),
            result_data.get("priority_score", 0),
            result_data.get("rtql_stage", 0),
            json.dumps(result_data.get("certificates", {})),
            json.dumps(result_data.get("blocking_gates", [])),
            result_data.get("interaction_count", 0),
            result_data.get("avg_nocs", 0),
            result_data.get("total_compensation", 0),
            json.dumps(result_data.get("full_result", {})),
        ))
        self.conn.commit()
        return result_id

    def get_pipeline_results(self, prospect_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pipeline results for a prospect, most recent first."""
        rows = self.conn.execute(
            "SELECT * FROM pipeline_results WHERE prospect_id = ? ORDER BY run_at DESC LIMIT ?",
            (prospect_id, limit)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── SEGMENT ASSIGNMENTS ───────────────────────────────────────

    def store_segment_assignment(self, prospect_id: str, segment_data: Dict[str, Any]) -> int:
        """Store a segment assignment."""
        cursor = self.conn.execute("""
            INSERT INTO segment_assignments (
                prospect_id, segment_id, segment_name, priority_tier,
                brand_experience_score, fit_score
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            prospect_id,
            segment_data.get("segment_id", ""),
            segment_data.get("segment_name", ""),
            segment_data.get("priority_tier", 2),
            segment_data.get("brand_experience_score"),
            segment_data.get("fit_score"),
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_segment_assignments(self, prospect_id: str) -> List[Dict[str, Any]]:
        """Get segment assignments for a prospect."""
        rows = self.conn.execute(
            "SELECT * FROM segment_assignments WHERE prospect_id = ? ORDER BY assigned_at DESC",
            (prospect_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── SILENCE EVALUATIONS ───────────────────────────────────────

    def store_silence_evaluation(self, data: Dict[str, Any]) -> str:
        """Store a silence recovery evaluation."""
        eval_id = data.get("eval_id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()

        self.conn.execute("""
            INSERT INTO silence_evaluations (
                eval_id, lead_id, evaluated_at, priority_score, selected_action,
                authority_level, policy_gate_result, executed, executed_at,
                execution_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            eval_id,
            data.get("lead_id", ""),
            now,
            data.get("priority_score", 0),
            data.get("selected_action", "do_not_execute"),
            data.get("authority_level", "D1"),
            data.get("policy_gate_result", "approved"),
            1 if data.get("executed") else 0,
            data.get("executed_at"),
            data.get("execution_result", ""),
        ))
        self.conn.commit()
        return eval_id

    def get_daily_action_count(self) -> int:
        """Count actions executed today (for daily limit enforcement)."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM silence_evaluations WHERE executed=1 AND executed_at LIKE ?",
            (f"{today}%",)
        ).fetchone()
        return row["cnt"] if row else 0

    # ── UTILITIES ─────────────────────────────────────────────────

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a sqlite3.Row to dict, deserializing JSON fields."""
        d = dict(row)
        # Deserialize JSON list/dict fields
        for key in d:
            if isinstance(d[key], str):
                if d[key].startswith("[") or d[key].startswith("{"):
                    try:
                        d[key] = json.loads(d[key])
                    except (json.JSONDecodeError, ValueError):
                        pass
            # Convert SQLite integers to booleans for boolean-like fields
            if key in ("converted", "abandoned", "escalated", "executed"):
                d[key] = bool(d[key])
        return d

    def count_table(self, table: str) -> int:
        """Count rows in a table."""
        row = self.conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
        return row["cnt"] if row else 0
