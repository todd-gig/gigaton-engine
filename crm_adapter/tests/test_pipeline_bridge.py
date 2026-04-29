"""Tests for CRM ↔ Pipeline Bridge."""

import sys
import os
import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from crm_adapter.engines.database import Database
from crm_adapter.engines.pipeline_bridge import PipelineBridge


@pytest.fixture
def bridge():
    """Create an in-memory database + bridge for testing."""
    db = Database(db_path=":memory:")
    b = PipelineBridge(db)
    yield b
    db.close()


def _seed_prospect(bridge, prospect_id="p001", with_brand=False, with_interactions=False):
    """Seed a prospect with optional brand and interaction data."""
    data = {
        "prospect_id": prospect_id,
        "domain": "example.com",
        "official_name": "Example Corp",
        "industries": ["technology", "saas"],
        "buyer_personas": ["VP Marketing"],
        "gtm_motion": "sales_led",
        "pricing_visibility": "contact_sales",
        "marketing_maturity": "medium",
        "sales_complexity": "high",
    }
    if with_brand:
        data.update({
            "brand_id": "b001",
            "brand_name": "Example Brand",
            "brand_tagline": "Building the future",
            "brand_mission": "Empower businesses",
            "brand_value_propositions": ["Speed", "Reliability"],
            "brand_differentiators": ["AI-powered", "Human-centered"],
            "brand_proof_assets": ["Case study A"],
            "brand_active_channels": ["email", "web", "social"],
            "brand_target_conversion_rate": 0.20,
        })
    bridge.db.upsert_prospect(data)

    if with_interactions:
        for i in range(3):
            bridge.db.add_interaction({
                "prospect_id": prospect_id,
                "channel": ["email", "web", "phone"][i],
                "status": "resolved",
                "response_time_seconds": 120.0 + i * 30,
                "resolution_time_seconds": 600.0 + i * 100,
                "converted": i == 2,
                "sentiment_score": 0.6 + i * 0.1,
                "trust_shift_score": 0.05 * i,
            })


class TestProspectConversion:
    def test_prospect_to_profile(self, bridge):
        _seed_prospect(bridge)
        row = bridge.db.get_prospect("p001")
        profile = bridge.prospect_to_profile(row)
        assert profile.prospect_id == "p001"
        assert profile.domain == "example.com"
        assert profile.official_name == "Example Corp"
        assert "technology" in profile.industries

    def test_prospect_to_brand_profile_with_brand(self, bridge):
        _seed_prospect(bridge, with_brand=True)
        row = bridge.db.get_prospect("p001")
        brand = bridge.prospect_to_brand_profile(row)
        assert brand is not None
        assert brand.brand_id == "b001"
        assert brand.brand_name == "Example Brand"
        assert "Speed" in brand.value_propositions

    def test_prospect_to_brand_profile_without_brand(self, bridge):
        _seed_prospect(bridge, with_brand=False)
        row = bridge.db.get_prospect("p001")
        brand = bridge.prospect_to_brand_profile(row)
        assert brand is None

    def test_interaction_conversion(self, bridge):
        _seed_prospect(bridge, with_interactions=True)
        rows = bridge.db.get_interactions("p001")
        events = bridge.interaction_rows_to_events(rows)
        assert len(events) == 3
        assert events[0].channel in ("email", "web", "phone")


class TestPipelineExecution:
    def test_run_pipeline_for_prospect(self, bridge):
        _seed_prospect(bridge, with_brand=True, with_interactions=True)
        result = bridge.run_pipeline_for_prospect("p001")
        assert result is not None
        assert result.prospect_id == "p001"
        assert result.verdict != ""
        assert result.interaction_count == 3

        # Check result was stored
        stored = bridge.db.get_pipeline_results("p001")
        assert len(stored) == 1
        assert stored[0]["verdict"] == result.verdict

    def test_run_pipeline_nonexistent(self, bridge):
        result = bridge.run_pipeline_for_prospect("nope")
        assert result is None

    def test_run_pipeline_without_brand(self, bridge):
        _seed_prospect(bridge, with_brand=False, with_interactions=True)
        result = bridge.run_pipeline_for_prospect("p001")
        assert result is not None
        # Should use default brand
        assert result.brand_coherence_coefficient > 0

    def test_run_pipeline_without_interactions(self, bridge):
        _seed_prospect(bridge, with_brand=True, with_interactions=False)
        result = bridge.run_pipeline_for_prospect("p001")
        assert result is not None
        assert result.interaction_count == 0


class TestSegmentationExecution:
    def test_classify_prospect(self, bridge):
        _seed_prospect(bridge, with_brand=True, with_interactions=True)
        segments = bridge.classify_prospect("p001")
        assert segments is not None
        assert isinstance(segments, list)

        # Check assignments stored
        stored = bridge.db.get_segment_assignments("p001")
        assert len(stored) == len(segments)

    def test_classify_nonexistent(self, bridge):
        result = bridge.classify_prospect("nope")
        assert result is None


class TestBatchPipeline:
    def test_batch_run(self, bridge):
        for i in range(3):
            _seed_prospect(bridge, prospect_id=f"p{i}", with_brand=True, with_interactions=True)
        stats = bridge.run_batch_pipeline(limit=10)
        assert stats["total"] == 3
        assert stats["processed"] == 3
        assert stats["errors"] == 0
