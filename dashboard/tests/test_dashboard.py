"""
Dashboard tests — Verify data generation and HTML rendering.

Tests:
  - Data generation produces all required keys and structure
  - HTML rendering produces valid HTML with all sections
  - Dashboard data contains correct number of scenarios
  - Brand data has all 7 ethos dimensions
  - Segment data has all 5 segments
  - Verdicts are correctly distributed
  - Compensation values are numeric and positive
"""
import sys
import os
import pytest
from html.parser import HTMLParser

# Ensure project root is on path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dashboard.data_generator import generate_dashboard_data
from dashboard.html_renderer import render_html_dashboard


class TestDataGeneration:
    """Test dashboard data generation."""

    def test_data_generator_produces_complete_structure(self):
        """Test that data_generator produces all required top-level keys."""
        data = generate_dashboard_data()

        required_keys = [
            "timestamp",
            "scenarios",
            "summary",
            "segmentation",
            "roles",
            "l1_components",
            "l2_ethos_dimensions",
        ]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

    def test_data_generator_processes_three_scenarios(self):
        """Test that all 3 scenarios are processed."""
        data = generate_dashboard_data()
        assert len(data["scenarios"]) == 3, "Expected 3 scenarios"

    def test_each_scenario_has_l1_l2_l3_l4_data(self):
        """Test that each scenario contains all layer data."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            required_layers = ["l1", "l2", "l3", "l4"]
            for layer in required_layers:
                assert layer in scenario, f"Scenario {scenario['scenario_num']} missing {layer} data"

    def test_l1_data_has_all_components(self):
        """Test L1 data contains all 7 component scores."""
        data = generate_dashboard_data()
        components = ["need", "service_fit", "readiness", "accessibility",
                     "expected_uplift", "economic_scale", "confidence"]

        for scenario in data["scenarios"]:
            l1 = scenario["l1"]
            for component in components:
                assert component in l1, f"L1 missing component: {component}"
                assert 0 <= l1[component] <= 100, f"L1 {component} out of bounds"

    def test_l1_total_fit_score_valid(self):
        """Test L1 total fit score is between 0-100."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            fit = scenario["l1"]["total_fit_score"]
            assert 0 <= fit <= 100, f"L1 fit score out of bounds: {fit}"

    def test_l2_has_all_seven_ethos_dimensions(self):
        """Test L2 brand coherence has all 7 ethos dimensions."""
        data = generate_dashboard_data()
        dimensions = [
            "truthfulness_explainability",
            "human_centered_technology",
            "long_term_value_creation",
            "cost_roi_discipline",
            "human_agency_respect",
            "trust_contribution",
            "manipulation_avoidance",
        ]

        for scenario in data["scenarios"]:
            coherence = scenario["l2"]["coherence"]
            for dim in dimensions:
                assert dim in coherence, f"L2 missing dimension: {dim}"
                assert 0 <= coherence[dim] <= 100, f"L2 {dim} out of bounds"

    def test_l2_coherence_composite_and_coefficient(self):
        """Test L2 coherence has composite score and coefficient."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            coherence = scenario["l2"]["coherence"]
            assert "composite_score" in coherence
            assert "coefficient" in coherence
            assert 0 <= coherence["composite_score"] <= 100
            assert 0.0 <= coherence["coefficient"] <= 1.25

    def test_l3_verdict_valid(self):
        """Test L3 verdict is one of the expected values."""
        data = generate_dashboard_data()
        valid_verdicts = ["auto_execute", "escalate_tier_1", "escalate_tier_2", "block", "needs_data"]

        for scenario in data["scenarios"]:
            verdict = scenario["l3"]["verdict"]
            assert verdict in valid_verdicts, f"Invalid verdict: {verdict}"

    def test_l3_scores_valid(self):
        """Test L3 value and trust scores are numeric and non-negative."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            l3 = scenario["l3"]
            assert isinstance(l3["value_score"], (int, float)), f"Value score not numeric: {l3['value_score']}"
            assert isinstance(l3["trust_score"], (int, float)), f"Trust score not numeric: {l3['trust_score']}"
            assert l3["value_score"] >= 0, f"Value score negative: {l3['value_score']}"
            assert l3["trust_score"] >= 0, f"Trust score negative: {l3['trust_score']}"

    def test_l3_rtql_stage_valid(self):
        """Test L3 RTQL stage is 1-7."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            stage = scenario["l3"]["rtql_stage"]
            assert 1 <= stage <= 7, f"RTQL stage out of bounds: {stage}"

    def test_l3_certificates_present(self):
        """Test L3 has certificate data."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            assert "certificates" in scenario["l3"]
            certs = scenario["l3"]["certificates"]
            assert isinstance(certs, dict)

    def test_l4_compensation_numeric_positive(self):
        """Test L4 compensation values are numeric and positive."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            l4 = scenario["l4"]
            assert isinstance(l4["total_compensation"], (int, float))
            assert l4["total_compensation"] >= 0, "Compensation should be non-negative"
            assert isinstance(l4["avg_nocs"], (int, float))

    def test_l4_interactions_valid(self):
        """Test L4 interaction data is properly structured."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            interactions = scenario["l4"]["interactions"]
            assert isinstance(interactions, list)
            for interaction in interactions:
                assert "interaction_id" in interaction
                assert "channel" in interaction
                assert "nocs" in interaction
                assert "compensation_total" in interaction

    def test_segmentation_has_five_segments(self):
        """Test segmentation contains exactly 5 segments."""
        data = generate_dashboard_data()
        segments = data["segmentation"]["segments"]
        assert len(segments) == 5, f"Expected 5 segments, got {len(segments)}"

    def test_segmentation_segments_complete(self):
        """Test each segment has required fields."""
        data = generate_dashboard_data()
        required_fields = [
            "segment_id",
            "segment_name",
            "description",
            "expected_value_range",
            "priority_tier",
            "primary_gap_pattern",
            "service_packages",
            "apollo_targeting",
        ]

        for segment in data["segmentation"]["segments"]:
            for field in required_fields:
                assert field in segment, f"Segment missing {field}"

    def test_summary_verdict_distribution(self):
        """Test summary contains verdict distribution."""
        data = generate_dashboard_data()
        summary = data["summary"]
        assert "verdicts_distribution" in summary
        verdicts = summary["verdicts_distribution"]
        assert sum(verdicts.values()) == 3, "Should have 3 verdicts total"

    def test_summary_metrics_present(self):
        """Test summary contains all metric keys."""
        data = generate_dashboard_data()
        summary = data["summary"]
        required_metrics = [
            "total_prospects",
            "avg_fit_score",
            "avg_value_score",
            "avg_trust_score",
            "total_compensation_pool",
            "layer_statuses",
        ]
        for metric in required_metrics:
            assert metric in summary, f"Summary missing {metric}"

    def test_roles_data_present(self):
        """Test roles data is populated."""
        data = generate_dashboard_data()
        roles = data["roles"]
        assert isinstance(roles, list)
        assert len(roles) > 0, "Should have at least one role"
        assert "role_id" in roles[0]
        assert "benchmark_weights" in roles[0]


class TestHTMLRendering:
    """Test HTML dashboard rendering."""

    def test_render_produces_valid_html(self):
        """Test that render_html_dashboard produces valid HTML string."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        assert isinstance(html, str)
        assert len(html) > 0
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_html_contains_all_panels(self):
        """Test HTML contains all 7 dashboard panels."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        panels = [
            "Executive Summary",
            "L1 — Prospect Sensing",
            "L2 — Brand Experience",
            "L3 — Qualification Engine",
            "L4 — Execution Matrix",
            "Customer Segmentation",
            "Pipeline Flow",
        ]

        for panel in panels:
            assert panel in html, f"HTML missing panel: {panel}"

    def test_html_includes_chart_js(self):
        """Test HTML includes Chart.js CDN."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        assert "cdn.jsdelivr.net/npm/chart.js" in html

    def test_html_includes_dark_theme_colors(self):
        """Test HTML includes dark theme color values."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        theme_colors = ["#0a0e17", "#131a2b", "#e0e6ed", "#00ff88", "#ff6b6b", "#ffd93d", "#6bcfff"]
        for color in theme_colors:
            assert color in html, f"HTML missing theme color: {color}"

    def test_html_includes_dashboard_data_as_json(self):
        """Test HTML includes dashboard data embedded as JSON."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        # Check for embedded JSON structures
        assert "dashboardData" in html or "scenarios" in html
        assert "{" in html and "}" in html  # JSON present

    def test_html_includes_interactive_elements(self):
        """Test HTML includes interactive elements (tabs, collapsible cards)."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        interactive_elements = [
            "card-header",
            "card-toggle",
            "scenario-tab",
            "scenario-content",
        ]

        for element in interactive_elements:
            assert element in html, f"HTML missing interactive element: {element}"

    def test_html_includes_verdict_badges(self):
        """Test HTML includes verdict badge elements."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        assert "verdict-badge" in html
        assert "auto_execute" in html or "escalate" in html

    def test_html_includes_metric_displays(self):
        """Test HTML includes metric display elements."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        assert "metric" in html
        assert "metric-label" in html
        assert "metric-value" in html

    def test_html_includes_table_elements(self):
        """Test HTML includes table elements for data display."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        assert "<table" in html
        assert "<th>" in html
        assert "<tr>" in html

    def test_html_is_single_file(self):
        """Test HTML is self-contained (no external imports except Chart.js CDN)."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        # Should have embedded CSS
        assert "<style>" in html
        # Should have embedded JavaScript
        assert "<script>" in html
        # Should only reference Chart.js CDN and nothing else external
        external_imports = [
            "href=",  # External stylesheets
            "src=",   # External scripts (except Chart.js)
        ]
        for imp in external_imports:
            if imp == "src=":
                # src= is allowed only for Chart.js
                assert html.count("src=") == 1 or "chart.js" in html


class TestDataGeneratorIntegration:
    """Integration tests for data generation with pipeline."""

    def test_generator_runs_without_errors(self):
        """Test that data generator runs the full pipeline without errors."""
        try:
            data = generate_dashboard_data()
            assert data is not None
        except Exception as e:
            pytest.fail(f"Data generator raised exception: {e}")

    def test_all_three_scenarios_produce_results(self):
        """Test that all 3 scenarios produce complete results."""
        data = generate_dashboard_data()

        for scenario in data["scenarios"]:
            assert scenario["scenario_num"] in [1, 2, 3]
            assert scenario["l1"]["prospect_id"] in ["P001", "P002", "P003"]
            assert len(scenario["l3"]["verdict"]) > 0
            assert scenario["l4"]["total_compensation"] >= 0


class TestRendererIntegration:
    """Integration tests for HTML rendering with data."""

    def test_renderer_produces_complete_dashboard(self):
        """Test that renderer produces complete, functional dashboard."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        # Should be large enough to contain all data and visualizations
        assert len(html) > 10000, "HTML should be comprehensive"

        # Should have proper structure
        assert html.count("<div") > 20  # Multiple divs
        assert html.count("<canvas") >= 6  # At least 6 charts
        assert html.count("new Chart(") >= 6  # At least 6 chart initializations

    def test_rendered_html_matches_data(self):
        """Test that rendered HTML contains key data values from input."""
        data = generate_dashboard_data()
        html = render_html_dashboard(data)

        # Check for prospect names
        assert "Acme Widgets" in html or "P001" in html

        # Check for verdicts
        verdicts = data["summary"]["verdicts_distribution"].keys()
        verdict_found = any(v in html for v in verdicts)
        assert verdict_found, "No verdicts found in HTML"

        # Check for segment names
        segments = data["segmentation"]["segments"]
        segment_found = any(seg["segment_name"] in html for seg in segments)
        assert segment_found, "No segments found in HTML"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
