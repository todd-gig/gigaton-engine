"""CRM ↔ Pipeline Bridge — converts database records to pipeline objects and back.

Reads prospects/interactions from the CRM database, builds pipeline-compatible
objects (ProspectProfile, BrandProfile, InteractionEvent), runs the L1→L2→L3→L4
pipeline, and stores results back in the database.

This is the integration layer between the internal FE database and the
Gigaton intelligence pipeline.
"""

import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

_ENGINE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _ENGINE_ROOT)

from crm_adapter.engines.database import Database

from l1_sensing.models.prospect import (
    ProspectProfile, CapabilitySummary, MaturityLevel, GTMMotion, PricingVisibility,
)
from l1_sensing.models.inference import InferenceRecord, InferenceType
from l2_brand_experience.models.brand_profile import BrandProfile
from l4_execution.models.interaction import InteractionEvent
from pipeline.engine import GigatonEngine, PipelineResult
from segmentation.engines.segmentation_engine import (
    SegmentationEngine, InteractionPerformanceContext,
)
from l2_brand_experience.engines.brand_experience_engine import BrandExperienceEngine


# ── Maturity/enum converters ─────────────────────────────────────

_MATURITY_MAP = {
    "unknown": MaturityLevel.UNKNOWN, "low": MaturityLevel.LOW,
    "medium": MaturityLevel.MEDIUM, "high": MaturityLevel.HIGH,
}

_GTM_MAP = {
    "unknown": GTMMotion.UNKNOWN, "sales_led": GTMMotion.SALES_LED,
    "plg": GTMMotion.PLG, "hybrid": GTMMotion.HYBRID,
}

_PRICING_MAP = {
    "unknown": PricingVisibility.UNKNOWN, "public": PricingVisibility.PUBLIC,
    "contact_sales": PricingVisibility.CONTACT_SALES,
}

_INFERENCE_TYPE_MAP = {
    "pain_point": InferenceType.PAIN_POINT,
    "service_fit": InferenceType.SERVICE_FIT,
    "value_estimate": InferenceType.VALUE_ESTIMATE,
    "business_goal": InferenceType.BUSINESS_GOAL,
    "gtm_motion": InferenceType.GTM_MOTION,
}


class PipelineBridge:
    """Bridges CRM database records to/from Gigaton pipeline objects.

    Responsibilities:
      1. Convert DB prospect dict → ProspectProfile + BrandProfile
      2. Convert DB interaction dicts → List[InteractionEvent]
      3. Convert DB inference dicts → List[InferenceRecord]
      4. Run pipeline and store results back to DB
      5. Run segmentation and store segment assignments
    """

    def __init__(self, db: Database, engine: Optional[GigatonEngine] = None):
        self.db = db
        self.engine = engine or GigatonEngine()
        self.segmentation = SegmentationEngine()

    # ── DB → Pipeline Object Converters ──────────────────────────

    def prospect_to_profile(self, row: Dict[str, Any]) -> ProspectProfile:
        """Convert a database prospect row to a ProspectProfile."""
        industries = row.get("industries", [])
        if isinstance(industries, str):
            import json
            try:
                industries = json.loads(industries)
            except (json.JSONDecodeError, ValueError):
                industries = []

        buyer_personas = row.get("buyer_personas", [])
        if isinstance(buyer_personas, str):
            import json
            try:
                buyer_personas = json.loads(buyer_personas)
            except (json.JSONDecodeError, ValueError):
                buyer_personas = []

        service_geos = row.get("service_geographies", [])
        if isinstance(service_geos, str):
            import json
            try:
                service_geos = json.loads(service_geos)
            except (json.JSONDecodeError, ValueError):
                service_geos = []

        evidence_ids = row.get("evidence_ids", [])
        if isinstance(evidence_ids, str):
            import json
            try:
                evidence_ids = json.loads(evidence_ids)
            except (json.JSONDecodeError, ValueError):
                evidence_ids = []

        caps = CapabilitySummary(
            marketing_maturity=_MATURITY_MAP.get(
                row.get("marketing_maturity", "low"), MaturityLevel.LOW
            ),
            sales_complexity=_MATURITY_MAP.get(
                row.get("sales_complexity", "medium"), MaturityLevel.MEDIUM
            ),
            measurement_maturity=_MATURITY_MAP.get(
                row.get("measurement_maturity", "low"), MaturityLevel.LOW
            ),
            interaction_management_maturity=_MATURITY_MAP.get(
                row.get("interaction_management_maturity", "low"), MaturityLevel.LOW
            ),
        )

        return ProspectProfile(
            prospect_id=row.get("prospect_id", ""),
            domain=row.get("domain", ""),
            official_name=row.get("official_name", ""),
            industries=industries,
            buyer_personas=buyer_personas,
            service_geographies=service_geos,
            gtm_motion=_GTM_MAP.get(row.get("gtm_motion", "unknown"), GTMMotion.UNKNOWN),
            pricing_visibility=_PRICING_MAP.get(
                row.get("pricing_visibility", "unknown"), PricingVisibility.UNKNOWN
            ),
            capability_summary=caps,
            last_verified_at=row.get("last_verified_at", ""),
            evidence_ids=evidence_ids,
        )

    def prospect_to_brand_profile(self, row: Dict[str, Any]) -> Optional[BrandProfile]:
        """Extract BrandProfile from a prospect's embedded brand fields.

        Returns None if no brand data is present (brand_id empty or 'default').
        """
        brand_id = row.get("brand_id", "")
        if not brand_id or brand_id == "default":
            return None

        # Parse JSON list fields
        def _parse_list(val):
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                import json
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    return []
            return []

        return BrandProfile(
            brand_id=brand_id,
            brand_name=row.get("brand_name", ""),
            tagline=row.get("brand_tagline", ""),
            mission=row.get("brand_mission", ""),
            value_propositions=_parse_list(row.get("brand_value_propositions", "[]")),
            differentiators=_parse_list(row.get("brand_differentiators", "[]")),
            proof_assets=_parse_list(row.get("brand_proof_assets", "[]")),
            compliance_claims=_parse_list(row.get("brand_compliance_claims", "[]")),
            certifications=_parse_list(row.get("brand_certifications", "[]")),
            active_channels=_parse_list(row.get("brand_active_channels", '["email","web"]')),
            target_response_time_seconds=row.get("brand_target_response_time", 300.0),
            target_resolution_time_seconds=row.get("brand_target_resolution_time", 3600.0),
            target_conversion_rate=row.get("brand_target_conversion_rate", 0.15),
            minimum_ethos_score=row.get("brand_minimum_ethos_score", 50.0),
        )

    def interaction_rows_to_events(
        self, rows: List[Dict[str, Any]]
    ) -> List[InteractionEvent]:
        """Convert database interaction rows to InteractionEvent objects."""
        events = []
        for row in rows:
            events.append(InteractionEvent(
                interaction_id=row.get("interaction_id", ""),
                entity_id=row.get("entity_id", "agent_01"),
                channel=row.get("channel", "email"),
                timestamp=row.get("timestamp", datetime.utcnow().isoformat()),
                status=row.get("status", "open"),
                response_time_seconds=row.get("response_time_seconds"),
                resolution_time_seconds=row.get("resolution_time_seconds"),
                converted=bool(row.get("converted", False)),
                abandoned=bool(row.get("abandoned", False)),
                escalated=bool(row.get("escalated", False)),
                sentiment_score=row.get("sentiment_score", 0.5),
                trust_shift_score=row.get("trust_shift_score", 0.0),
            ))
        return events

    def inference_rows_to_records(
        self, rows: List[Dict[str, Any]]
    ) -> List[InferenceRecord]:
        """Convert database inference rows to InferenceRecord objects."""
        records = []
        for row in rows:
            inf_type = _INFERENCE_TYPE_MAP.get(
                row.get("inference_type", "pain_point"), InferenceType.PAIN_POINT
            )
            evidence_ids = row.get("evidence_ids", [])
            if isinstance(evidence_ids, str):
                import json
                try:
                    evidence_ids = json.loads(evidence_ids)
                except (json.JSONDecodeError, ValueError):
                    evidence_ids = []

            records.append(InferenceRecord(
                object_id=row.get("object_id", ""),
                prospect_id=row.get("prospect_id", ""),
                inference_type=inf_type,
                statement=row.get("statement", ""),
                confidence=row.get("confidence", 0.5),
                evidence_ids=evidence_ids,
            ))
        return records

    # ── Pipeline Execution ───────────────────────────────────────

    def run_pipeline_for_prospect(
        self,
        prospect_id: str,
        role_key: str = "sales_operator",
        base_compensation: float = 5000.0,
        strategic_multiplier: float = 1.0,
    ) -> Optional[PipelineResult]:
        """Load prospect from DB, run full L1→L2→L3→L4 pipeline, store results.

        Args:
            prospect_id: The prospect to process
            role_key: Role profile for NOCS weighting
            base_compensation: Base compensation for the period
            strategic_multiplier: Strategy multiplier

        Returns:
            PipelineResult if prospect found, None otherwise
        """
        # Load prospect
        prospect_row = self.db.get_prospect(prospect_id)
        if prospect_row is None:
            return None

        # Convert to pipeline objects
        profile = self.prospect_to_profile(prospect_row)
        brand_profile = self.prospect_to_brand_profile(prospect_row)

        # Load interactions from DB
        interaction_rows = self.db.get_interactions(prospect_id)
        interactions = self.interaction_rows_to_events(interaction_rows)

        # Load inferences from DB
        inference_rows = self.db.conn.execute(
            "SELECT * FROM inferences WHERE prospect_id = ?", (prospect_id,)
        ).fetchall()
        inferences = self.inference_rows_to_records(
            [dict(r) for r in inference_rows]
        )

        # Run pipeline
        result = self.engine.run(
            prospect=profile,
            inferences=inferences,
            interactions=interactions,
            brand_profile=brand_profile,
            role_key=role_key,
            base_compensation=base_compensation,
            strategic_multiplier=strategic_multiplier,
        )

        # Store pipeline result in DB
        self.db.store_pipeline_result(prospect_id, {
            "fit_score": result.prospect_assessment.total,
            "need_score": result.prospect_assessment.need,
            "service_fit_score": result.prospect_assessment.service_fit,
            "readiness_score": result.prospect_assessment.readiness,
            "brand_experience_score": (
                result.brand_assessment.brand_experience_score
                if result.brand_assessment else None
            ),
            "brand_coherence_coefficient": result.brand_coherence_coefficient,
            "verdict": result.verdict,
            "value_score": result.value_score,
            "trust_score": result.trust_score,
            "priority_score": result.priority_score,
            "rtql_stage": result.rtql_stage,
            "certificates": result.certificates,
            "blocking_gates": result.blocking_gates,
            "interaction_count": result.interaction_count,
            "avg_nocs": result.avg_nocs,
            "total_compensation": result.total_compensation,
            "full_result": result.summary(),
        })

        return result

    def classify_prospect(
        self, prospect_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Load prospect from DB, run segmentation, store assignments.

        Returns list of matched segment dicts, or None if prospect not found.
        """
        prospect_row = self.db.get_prospect(prospect_id)
        if prospect_row is None:
            return None

        profile = self.prospect_to_profile(prospect_row)
        brand_profile = self.prospect_to_brand_profile(prospect_row)

        # Load interactions for context
        interaction_rows = self.db.get_interactions(prospect_id)
        interactions = self.interaction_rows_to_events(interaction_rows)

        # Load inferences
        inference_rows = self.db.conn.execute(
            "SELECT * FROM inferences WHERE prospect_id = ?", (prospect_id,)
        ).fetchall()
        inferences = self.inference_rows_to_records(
            [dict(r) for r in inference_rows]
        )

        # L1 assessment
        from l1_sensing.engines.prospect_value_engine import ProspectValueEngine
        assessment = ProspectValueEngine.score_prospect(profile, inferences)

        # L2 brand assessment (optional)
        brand_assessment = None
        if brand_profile is not None:
            brand_assessment = BrandExperienceEngine.assess(brand_profile, interactions)

        # L4 interaction context (optional)
        interaction_context = None
        if interactions:
            interaction_context = InteractionPerformanceContext.from_interactions(
                interactions
            )

        # Classify
        segments = self.segmentation.classify(
            profile, assessment, brand_assessment, interaction_context,
        )

        # Store segment assignments
        result_list = []
        for seg in segments:
            self.db.store_segment_assignment(prospect_id, {
                "segment_id": seg.segment_id,
                "segment_name": seg.segment_name,
                "priority_tier": seg.priority_tier,
                "brand_experience_score": (
                    brand_assessment.brand_experience_score
                    if brand_assessment else None
                ),
                "fit_score": assessment.total,
            })
            result_list.append({
                "segment_id": seg.segment_id,
                "segment_name": seg.segment_name,
                "priority_tier": seg.priority_tier,
                "gap_pattern": seg.primary_gap_pattern,
                "service_packages": seg.service_package_fit,
            })

        return result_list

    def run_batch_pipeline(
        self,
        limit: int = 100,
        role_key: str = "sales_operator",
    ) -> Dict[str, Any]:
        """Run pipeline for all prospects in the database.

        Returns summary stats of the batch run.
        """
        prospects = self.db.list_prospects(limit=limit)
        results = {"total": len(prospects), "processed": 0, "errors": 0, "verdicts": {}}

        for p in prospects:
            pid = p["prospect_id"]
            try:
                result = self.run_pipeline_for_prospect(pid, role_key=role_key)
                if result:
                    results["processed"] += 1
                    v = result.verdict
                    results["verdicts"][v] = results["verdicts"].get(v, 0) + 1
            except Exception as e:
                results["errors"] += 1
                results.setdefault("error_details", []).append({
                    "prospect_id": pid,
                    "error": str(e),
                })

        return results
