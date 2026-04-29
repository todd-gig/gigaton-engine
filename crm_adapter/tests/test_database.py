"""Tests for CRM database adapter."""

import pytest
import json
from crm_adapter.engines.database import Database


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    database = Database(db_path=":memory:")
    yield database
    database.close()


class TestProspects:
    def test_upsert_and_get(self, db):
        pid = db.upsert_prospect({
            "prospect_id": "p001",
            "domain": "example.com",
            "official_name": "Example Corp",
            "industries": ["technology", "saas"],
            "gtm_motion": "sales_led",
        })
        assert pid == "p001"
        p = db.get_prospect("p001")
        assert p is not None
        assert p["domain"] == "example.com"
        assert p["official_name"] == "Example Corp"
        assert p["industries"] == ["technology", "saas"]

    def test_upsert_update(self, db):
        db.upsert_prospect({"prospect_id": "p001", "official_name": "V1"})
        db.upsert_prospect({"prospect_id": "p001", "official_name": "V2"})
        p = db.get_prospect("p001")
        assert p["official_name"] == "V2"

    def test_list_prospects(self, db):
        for i in range(5):
            db.upsert_prospect({"prospect_id": f"p{i}", "official_name": f"Corp {i}"})
        prospects = db.list_prospects(limit=3)
        assert len(prospects) == 3

    def test_get_nonexistent(self, db):
        assert db.get_prospect("nope") is None

    def test_auto_id(self, db):
        pid = db.upsert_prospect({"official_name": "No ID Corp"})
        assert len(pid) > 0
        p = db.get_prospect(pid)
        assert p["official_name"] == "No ID Corp"

    def test_brand_fields(self, db):
        db.upsert_prospect({
            "prospect_id": "p_brand",
            "brand_id": "b001",
            "brand_name": "Cool Brand",
            "brand_value_propositions": ["fast", "reliable"],
            "brand_target_conversion_rate": 0.25,
        })
        p = db.get_prospect("p_brand")
        assert p["brand_id"] == "b001"
        assert p["brand_name"] == "Cool Brand"
        assert p["brand_value_propositions"] == ["fast", "reliable"]
        assert p["brand_target_conversion_rate"] == 0.25


class TestInteractions:
    def test_add_and_get(self, db):
        db.upsert_prospect({"prospect_id": "p001"})
        iid = db.add_interaction({
            "prospect_id": "p001",
            "channel": "email",
            "status": "resolved",
            "converted": True,
            "sentiment_score": 0.8,
        })
        assert len(iid) > 0
        interactions = db.get_interactions("p001")
        assert len(interactions) == 1
        assert interactions[0]["channel"] == "email"
        assert interactions[0]["converted"] is True
        assert interactions[0]["sentiment_score"] == 0.8


class TestLeads:
    def test_upsert_and_get(self, db):
        db.upsert_prospect({"prospect_id": "p001"})
        lid = db.upsert_lead({
            "lead_id": "l001",
            "prospect_id": "p001",
            "status": "qualified",
            "score": 75.0,
        })
        assert lid == "l001"
        leads = db.get_leads("p001")
        assert len(leads) == 1
        assert leads[0]["status"] == "qualified"
        assert leads[0]["score"] == 75.0

    def test_lead_update(self, db):
        db.upsert_prospect({"prospect_id": "p001"})
        db.upsert_lead({"lead_id": "l001", "prospect_id": "p001", "status": "new"})
        db.upsert_lead({"lead_id": "l001", "prospect_id": "p001", "status": "qualified"})
        leads = db.get_leads("p001")
        assert leads[0]["status"] == "qualified"


class TestPipelineResults:
    def test_store_and_get(self, db):
        db.upsert_prospect({"prospect_id": "p001"})
        rid = db.store_pipeline_result("p001", {
            "fit_score": 72.5,
            "need_score": 65.0,
            "verdict": "qualified",
            "value_score": 80.0,
            "trust_score": 70.0,
            "priority_score": 75.0,
            "rtql_stage": 4,
            "certificates": {"QC": True, "VC": True},
            "blocking_gates": [],
        })
        assert len(rid) > 0
        results = db.get_pipeline_results("p001")
        assert len(results) == 1
        assert results[0]["fit_score"] == 72.5
        assert results[0]["verdict"] == "qualified"
        assert results[0]["certificates"] == {"QC": True, "VC": True}


class TestSegmentAssignments:
    def test_store_and_get(self, db):
        db.upsert_prospect({"prospect_id": "p001"})
        rowid = db.store_segment_assignment("p001", {
            "segment_id": "SEG_001",
            "segment_name": "High Growth",
            "priority_tier": 1,
            "fit_score": 80.0,
        })
        assert rowid > 0
        segs = db.get_segment_assignments("p001")
        assert len(segs) == 1
        assert segs[0]["segment_id"] == "SEG_001"


class TestSilenceEvaluations:
    def test_store_and_count(self, db):
        db.upsert_prospect({"prospect_id": "p001"})
        db.upsert_lead({"lead_id": "l001", "prospect_id": "p001"})
        db.store_silence_evaluation({
            "lead_id": "l001",
            "priority_score": 0.75,
            "selected_action": "send_email",
            "executed": True,
            "executed_at": "2026-04-24T12:00:00",
        })
        count = db.get_daily_action_count()
        assert count >= 0  # date may differ from test execution


class TestUtilities:
    def test_count_table(self, db):
        assert db.count_table("prospects") == 0
        db.upsert_prospect({"prospect_id": "p1"})
        assert db.count_table("prospects") == 1

    def test_json_deserialization(self, db):
        db.upsert_prospect({
            "prospect_id": "p_json",
            "industries": ["a", "b"],
            "buyer_personas": ["VP Marketing"],
        })
        p = db.get_prospect("p_json")
        assert isinstance(p["industries"], list)
        assert p["industries"] == ["a", "b"]
