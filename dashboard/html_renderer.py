"""
HTML Dashboard Renderer — Generates single-file interactive dashboard.

Produces a self-contained HTML file with embedded CSS/JS using Chart.js
for all visualizations. Dark theme with accent colors optimized for
data visualization and readability.

Color scheme:
  - Background: #0a0e17
  - Cards: #131a2b
  - Text: #e0e6ed
  - Success: #00ff88
  - Failure: #ff6b6b
  - Warning: #ffd93d
  - Info: #6bcfff
"""
from typing import Dict, Any


def render_html_dashboard(data: Dict[str, Any]) -> str:
    """
    Render complete dashboard as single HTML string.

    Args:
        data: Dashboard data dict from generate_dashboard_data()

    Returns:
        Complete HTML string ready to write to file
    """

    # Extract data for easier reference
    scenarios = data.get("scenarios", [])
    summary = data.get("summary", {})
    segmentation = data.get("segmentation", {})
    roles = data.get("roles", [])

    # Build scenario data for JavaScript
    scenarios_json = _format_scenarios_for_js(scenarios)
    segments_json = _format_segments_for_js(segmentation.get("segments", []))
    summary_json = _format_summary_for_js(summary)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gigaton Engine — Pipeline Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #0a0e17 0%, #0f1625 100%);
            color: #e0e6ed;
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 24px;
        }}

        header {{
            margin-bottom: 32px;
            border-bottom: 2px solid rgba(107, 207, 255, 0.2);
            padding-bottom: 16px;
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #00ff88, #6bcfff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            color: #a0a6b0;
            font-size: 1rem;
        }}

        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }}

        .card {{
            background: #131a2b;
            border: 1px solid rgba(107, 207, 255, 0.15);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }}

        .card:hover {{
            border-color: rgba(107, 207, 255, 0.4);
            box-shadow: 0 8px 24px rgba(0, 255, 136, 0.1);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            cursor: pointer;
            user-select: none;
        }}

        .card-header h2 {{
            font-size: 1.4rem;
            color: #6bcfff;
            margin: 0;
            flex: 1;
        }}

        .card-toggle {{
            color: #a0a6b0;
            font-size: 1.2rem;
            transition: transform 0.3s ease;
        }}

        .card.collapsed .card-toggle {{
            transform: rotate(-90deg);
        }}

        .card-content {{
            display: block;
            animation: slideDown 0.3s ease;
        }}

        .card.collapsed .card-content {{
            display: none;
        }}

        @keyframes slideDown {{
            from {{
                opacity: 0;
                max-height: 0;
            }}
            to {{
                opacity: 1;
                max-height: 1000px;
            }}
        }}

        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding: 12px;
            background: rgba(6, 175, 233, 0.05);
            border-radius: 8px;
        }}

        .metric-label {{
            color: #a0a6b0;
            font-size: 0.9rem;
        }}

        .metric-value {{
            font-weight: bold;
            font-size: 1.1rem;
            color: #00ff88;
        }}

        .metric.warning .metric-value {{
            color: #ffd93d;
        }}

        .metric.critical .metric-value {{
            color: #ff6b6b;
        }}

        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: bold;
            margin-right: 8px;
            margin-bottom: 8px;
        }}

        .status-badge.healthy {{
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
        }}

        .status-badge.warning {{
            background: rgba(255, 217, 61, 0.2);
            color: #ffd93d;
        }}

        .status-badge.critical {{
            background: rgba(255, 107, 107, 0.2);
            color: #ff6b6b;
        }}

        .verdict-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: bold;
            margin-bottom: 12px;
        }}

        .verdict-badge.auto_execute {{
            background: rgba(0, 255, 136, 0.15);
            color: #00ff88;
            border: 1px solid #00ff88;
        }}

        .verdict-badge.escalate_tier_1 {{
            background: rgba(255, 217, 61, 0.15);
            color: #ffd93d;
            border: 1px solid #ffd93d;
        }}

        .verdict-badge.escalate_tier_2 {{
            background: rgba(255, 107, 107, 0.15);
            color: #ff6b6b;
            border: 1px solid #ff6b6b;
        }}

        .verdict-badge.needs_data {{
            background: rgba(107, 207, 255, 0.15);
            color: #6bcfff;
            border: 1px solid #6bcfff;
        }}

        .verdict-badge.block {{
            background: rgba(255, 107, 107, 0.2);
            color: #ff6b6b;
            border: 2px solid #ff6b6b;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 0.9rem;
        }}

        th {{
            background: rgba(107, 207, 255, 0.1);
            padding: 12px;
            text-align: left;
            color: #6bcfff;
            border-bottom: 2px solid rgba(107, 207, 255, 0.2);
            font-weight: bold;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid rgba(107, 207, 255, 0.1);
        }}

        tr:hover {{
            background: rgba(107, 207, 255, 0.05);
        }}

        .chart-container {{
            position: relative;
            height: 300px;
            margin: 20px 0;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        .gauge {{
            display: inline-block;
            width: 120px;
            height: 120px;
            margin: 10px;
            text-align: center;
        }}

        .gauge-label {{
            font-size: 0.8rem;
            color: #a0a6b0;
            margin-top: 8px;
        }}

        .gauge-value {{
            font-size: 1.4rem;
            font-weight: bold;
            color: #6bcfff;
        }}

        .scenario-tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}

        .scenario-tab {{
            padding: 8px 16px;
            background: rgba(107, 207, 255, 0.1);
            border: 1px solid rgba(107, 207, 255, 0.2);
            border-radius: 6px;
            cursor: pointer;
            color: #a0a6b0;
            transition: all 0.3s ease;
        }}

        .scenario-tab.active {{
            background: rgba(107, 207, 255, 0.3);
            color: #6bcfff;
            border-color: #6bcfff;
        }}

        .scenario-content {{
            display: none;
        }}

        .scenario-content.active {{
            display: block;
        }}

        .gap-pattern {{
            background: rgba(255, 217, 61, 0.1);
            border-left: 3px solid #ffd93d;
            padding: 12px;
            margin: 12px 0;
            border-radius: 4px;
            font-size: 0.9rem;
            color: #ffd93d;
        }}

        .service-package {{
            display: inline-block;
            background: rgba(0, 255, 136, 0.1);
            color: #00ff88;
            padding: 6px 12px;
            border-radius: 4px;
            margin: 4px 4px 4px 0;
            font-size: 0.85rem;
        }}

        .certificate {{
            display: inline-block;
            background: rgba(107, 207, 255, 0.15);
            color: #6bcfff;
            padding: 6px 12px;
            border-radius: 4px;
            margin-right: 8px;
            font-size: 0.85rem;
            border: 1px solid #6bcfff;
        }}

        .certificate.unchecked {{
            background: rgba(160, 166, 176, 0.05);
            color: #505860;
            border-color: #505860;
        }}

        footer {{
            text-align: center;
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid rgba(107, 207, 255, 0.1);
            color: #505860;
            font-size: 0.85rem;
        }}

        /* NIX Button */
        .nix-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(107, 207, 255, 0.2));
            border: 1px solid #00ff88;
            border-radius: 8px;
            color: #00ff88;
            font-size: 0.9rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 8px 4px;
        }}

        .nix-btn:hover {{
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.35), rgba(107, 207, 255, 0.35));
            box-shadow: 0 4px 16px rgba(0, 255, 136, 0.25);
            transform: translateY(-1px);
        }}

        .nix-btn .arrow {{
            font-size: 1.1rem;
        }}

        /* NIX Modal Overlay */
        .nix-modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            z-index: 1000;
            overflow-y: auto;
            padding: 40px 20px;
        }}

        .nix-modal-overlay.active {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .nix-modal {{
            max-width: 1200px;
            margin: 0 auto;
            background: #0f1625;
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 16px;
            padding: 32px;
            position: relative;
        }}

        .nix-modal-close {{
            position: absolute;
            top: 16px;
            right: 20px;
            background: none;
            border: 1px solid rgba(255, 107, 107, 0.4);
            color: #ff6b6b;
            font-size: 1.2rem;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 6px;
            transition: all 0.2s;
        }}

        .nix-modal-close:hover {{
            background: rgba(255, 107, 107, 0.2);
        }}

        .nix-header {{
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(107, 207, 255, 0.2);
        }}

        .nix-header h2 {{
            font-size: 1.8rem;
            background: linear-gradient(135deg, #00ff88, #6bcfff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }}

        .nix-strategy-box {{
            background: rgba(107, 207, 255, 0.08);
            border-left: 4px solid #6bcfff;
            padding: 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 24px;
        }}

        .nix-strategy-box .label {{
            color: #6bcfff;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}

        .nix-intent-badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.85rem;
            margin-right: 8px;
        }}

        .nix-intent-badge.proposal {{ background: rgba(0, 255, 136, 0.2); color: #00ff88; border: 1px solid #00ff88; }}
        .nix-intent-badge.value_demonstration {{ background: rgba(107, 207, 255, 0.2); color: #6bcfff; border: 1px solid #6bcfff; }}
        .nix-intent-badge.data_gathering {{ background: rgba(255, 217, 61, 0.2); color: #ffd93d; border: 1px solid #ffd93d; }}
        .nix-intent-badge.trust_building {{ background: rgba(255, 107, 107, 0.2); color: #ff6b6b; border: 1px solid #ff6b6b; }}
        .nix-intent-badge.nurture {{ background: rgba(160, 166, 176, 0.2); color: #a0a6b0; border: 1px solid #a0a6b0; }}

        .nix-urgency-badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.85rem;
        }}

        .nix-urgency-badge.immediate {{ background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }}
        .nix-urgency-badge.next_day {{ background: rgba(255, 217, 61, 0.2); color: #ffd93d; }}
        .nix-urgency-badge.this_week {{ background: rgba(107, 207, 255, 0.2); color: #6bcfff; }}
        .nix-urgency-badge.deferred {{ background: rgba(160, 166, 176, 0.2); color: #a0a6b0; }}

        /* Channel cards in NIX */
        .nix-channels-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }}

        .nix-channel-card {{
            background: #131a2b;
            border: 1px solid rgba(107, 207, 255, 0.15);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
        }}

        .nix-channel-card:hover {{
            border-color: rgba(0, 255, 136, 0.4);
        }}

        .nix-channel-card.rank-1 {{
            border-color: rgba(0, 255, 136, 0.4);
            box-shadow: 0 4px 16px rgba(0, 255, 136, 0.1);
        }}

        .nix-channel-card.rank-2 {{
            border-color: rgba(107, 207, 255, 0.3);
        }}

        .nix-channel-card .rank-badge {{
            position: absolute;
            top: -8px;
            right: 12px;
            background: #00ff88;
            color: #0a0e17;
            padding: 2px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
        }}

        .nix-channel-card.rank-2 .rank-badge {{ background: #6bcfff; }}
        .nix-channel-card.rank-3 .rank-badge {{ background: #ffd93d; }}

        .nix-channel-name {{
            font-size: 1.2rem;
            color: #e0e6ed;
            font-weight: bold;
            margin-bottom: 8px;
        }}

        .nix-confidence-bar {{
            height: 6px;
            background: rgba(107, 207, 255, 0.15);
            border-radius: 3px;
            margin: 8px 0 12px;
            overflow: hidden;
        }}

        .nix-confidence-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }}

        /* Editable fields in NIX */
        .nix-editable {{
            background: rgba(107, 207, 255, 0.05);
            border: 1px dashed rgba(107, 207, 255, 0.25);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            position: relative;
        }}

        .nix-editable .edit-label {{
            font-size: 0.75rem;
            color: #6bcfff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .nix-editable .edit-icon {{
            font-size: 0.7rem;
            opacity: 0.6;
        }}

        .nix-editable textarea,
        .nix-editable input[type="text"],
        .nix-editable select {{
            width: 100%;
            background: rgba(10, 14, 23, 0.8);
            border: 1px solid rgba(107, 207, 255, 0.2);
            border-radius: 6px;
            color: #e0e6ed;
            padding: 10px;
            font-family: inherit;
            font-size: 0.9rem;
            resize: vertical;
        }}

        .nix-editable textarea:focus,
        .nix-editable input:focus,
        .nix-editable select:focus {{
            outline: none;
            border-color: #00ff88;
            box-shadow: 0 0 8px rgba(0, 255, 136, 0.2);
        }}

        .nix-approve-btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 24px;
            background: linear-gradient(135deg, #00ff88, #00dd77);
            border: none;
            border-radius: 8px;
            color: #0a0e17;
            font-size: 0.95rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 8px;
        }}

        .nix-approve-btn:hover {{
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.4);
            transform: translateY(-1px);
        }}

        .nix-approve-btn.approved {{
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
            border: 1px solid #00ff88;
        }}

        .nix-talking-points li {{
            color: #a0a6b0;
            margin-bottom: 6px;
            padding-left: 4px;
        }}

        .nix-ethos-mini {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 6px;
            margin-top: 8px;
        }}

        .nix-ethos-item {{
            display: flex;
            justify-content: space-between;
            background: rgba(255, 217, 61, 0.05);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
        }}

        .nix-ethos-item .dim {{ color: #a0a6b0; }}
        .nix-ethos-item .val {{ color: #ffd93d; font-weight: bold; }}

        .nix-risk {{
            color: #ff6b6b;
            font-size: 0.85rem;
            padding: 4px 0;
        }}

        .nix-success-item {{
            color: #00ff88;
            font-size: 0.85rem;
            padding: 2px 0;
        }}

        @media (max-width: 1200px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}

            .nix-channels-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <h1>Gigaton Engine</h1>
            <p class="subtitle">Pipeline Dashboard — L1→L4 Intelligence Flow</p>
        </header>

        <!-- Dashboard Grid -->
        <div class="dashboard-grid">

            {_render_panel_executive_summary(summary)}
            {_render_panel_l1_sensing(scenarios)}
            {_render_panel_l2_brand_experience(scenarios)}
            {_render_panel_l3_qualification(scenarios)}
            {_render_panel_l4_execution(scenarios)}
            {_render_panel_segmentation(segmentation)}
            {_render_panel_pipeline_flow(scenarios, summary)}
            {_render_panel_nix(scenarios)}

        </div>
    </div>

    <!-- NIX Modal Overlay (one per scenario) -->
    {_render_nix_modals(scenarios)}

    <footer>
        <p>Gigaton Engine Pipeline Dashboard — Generated {data.get('timestamp', 'N/A')}</p>
        <p>L1 Sensing • L2 Brand Experience • L3 Qualification • L4 Execution</p>
    </footer>

    <!-- Chart.js Initialization -->
    <script>
        const Chart = window.Chart;
        const dashboardData = {scenarios_json};
        const segmentationData = {segments_json};
        const summaryData = {summary_json};

        // Initialize all charts
        initializeDashboard();

        function initializeDashboard() {{
            initL1RadarCharts();
            initL2EthosCharts();
            initL3DecisionMatrix();
            initL4CompensationWaterfall();
            initSegmentationChart();
            initPipelineFlow();
        }}

        // L1 Prospect Sensing - Radar Charts
        function initL1RadarCharts() {{
            dashboardData.scenarios.forEach((scenario, idx) => {{
                const canvasId = `l1-radar-${{idx}}`;
                const canvas = document.getElementById(canvasId);
                if (!canvas) return;

                const l1 = scenario.l1;
                const ctx = canvas.getContext('2d');
                new Chart(ctx, {{
                    type: 'radar',
                    data: {{
                        labels: ['Need', 'Service Fit', 'Readiness', 'Accessibility', 'Expected Uplift', 'Economic Scale', 'Confidence'],
                        datasets: [{{
                            label: scenario.l1.prospect_name,
                            data: [l1.need, l1.service_fit, l1.readiness, l1.accessibility, l1.expected_uplift, l1.economic_scale, l1.confidence],
                            borderColor: '#6bcfff',
                            backgroundColor: 'rgba(107, 207, 255, 0.15)',
                            pointBackgroundColor: '#00ff88',
                            pointBorderColor: '#e0e6ed',
                            fill: true,
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: true, labels: {{ color: '#a0a6b0' }} }}
                        }},
                        scales: {{
                            r: {{
                                min: 0,
                                max: 100,
                                ticks: {{ color: '#a0a6b0' }},
                                grid: {{ color: 'rgba(107, 207, 255, 0.1)' }},
                            }}
                        }}
                    }}
                }});
            }});
        }}

        // L2 Brand Experience - Ethos Radar
        function initL2EthosCharts() {{
            dashboardData.scenarios.forEach((scenario, idx) => {{
                const canvasId = `l2-ethos-${{idx}}`;
                const canvas = document.getElementById(canvasId);
                if (!canvas) return;

                const coherence = scenario.l2.coherence;
                const ctx = canvas.getContext('2d');
                new Chart(ctx, {{
                    type: 'radar',
                    data: {{
                        labels: ['Truthfulness', 'Human-Centered', 'Long-Term Value', 'Cost-ROI', 'Agency Respect', 'Trust', 'Anti-Manipulation'],
                        datasets: [{{
                            label: 'Ethos Dimensions',
                            data: [
                                coherence.truthfulness_explainability,
                                coherence.human_centered_technology,
                                coherence.long_term_value_creation,
                                coherence.cost_roi_discipline,
                                coherence.human_agency_respect,
                                coherence.trust_contribution,
                                coherence.manipulation_avoidance
                            ],
                            borderColor: '#ffd93d',
                            backgroundColor: 'rgba(255, 217, 61, 0.15)',
                            pointBackgroundColor: '#ff6b6b',
                            pointBorderColor: '#e0e6ed',
                            fill: true,
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: true, labels: {{ color: '#a0a6b0' }} }}
                        }},
                        scales: {{
                            r: {{
                                min: 0,
                                max: 100,
                                ticks: {{ color: '#a0a6b0' }},
                                grid: {{ color: 'rgba(107, 207, 255, 0.1)' }},
                            }}
                        }}
                    }}
                }});
            }});
        }}

        // L3 Decision Matrix - Value vs Trust Scatter
        function initL3DecisionMatrix() {{
            const canvasId = 'l3-value-trust-scatter';
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;

            const data = {{
                labels: [],
                datasets: []
            }};

            const verdictColors = {{
                'auto_execute': '#00ff88',
                'escalate_tier_1': '#ffd93d',
                'escalate_tier_2': '#ff6b6b',
                'needs_data': '#6bcfff',
                'block': '#ff6b6b'
            }};

            dashboardData.scenarios.forEach((scenario) => {{
                const color = verdictColors[scenario.l3.verdict] || '#a0a6b0';
                data.labels.push(scenario.l1.prospect_name);
            }});

            // Create dataset with each scenario as a point
            const points = dashboardData.scenarios.map((scenario) => {{
                const color = verdictColors[scenario.l3.verdict] || '#a0a6b0';
                return {{
                    x: scenario.l3.value_score,
                    y: scenario.l3.trust_score,
                    label: scenario.l1.prospect_name,
                    color: color
                }};
            }});

            const ctx = canvas.getContext('2d');
            new Chart(ctx, {{
                type: 'bubble',
                data: {{
                    datasets: [{{
                        label: 'Prospects',
                        data: points,
                        backgroundColor: points.map(p => p.color),
                        borderColor: points.map(p => p.color),
                        borderWidth: 2,
                        radius: 8,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.raw.label + ` (Value: ${{context.raw.x.toFixed(2)}}, Trust: ${{context.raw.y.toFixed(2)}})`;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            min: 0, max: 1.0,
                            title: {{ display: true, text: 'Value Score', color: '#a0a6b0' }},
                            ticks: {{ color: '#a0a6b0' }},
                            grid: {{ color: 'rgba(107, 207, 255, 0.1)' }},
                        }},
                        y: {{
                            min: 0, max: 1.0,
                            title: {{ display: true, text: 'Trust Score', color: '#a0a6b0' }},
                            ticks: {{ color: '#a0a6b0' }},
                            grid: {{ color: 'rgba(107, 207, 255, 0.1)' }},
                        }}
                    }}
                }}
            }});
        }}

        // L4 Compensation - Waterfall Chart
        function initL4CompensationWaterfall() {{
            const canvasId = 'l4-compensation-waterfall';
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;

            // Calculate aggregate compensation data
            let totalBase = 0, totalVariable = 0, totalEthos = 0;
            dashboardData.scenarios.forEach((scenario) => {{
                scenario.l4.interactions.forEach((interaction) => {{
                    totalBase += interaction.compensation_total * 0.6;  // Assume 60% base
                    totalVariable += interaction.compensation_variable;
                    totalEthos += (interaction.compensation_total - interaction.compensation_variable - totalBase * 0.6);
                }});
            }});

            const total = totalBase + totalVariable + totalEthos;

            const ctx = canvas.getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: ['Base', 'Variable', 'Ethos Adj.', 'Total'],
                    datasets: [{{
                        label: 'Compensation Components',
                        data: [totalBase, totalVariable, totalEthos, 0],
                        backgroundColor: ['#6bcfff', '#00ff88', '#ffd93d', '#ff6b6b'],
                        borderColor: ['#6bcfff', '#00ff88', '#ffd93d', '#ff6b6b'],
                        borderWidth: 2,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {{
                        legend: {{ display: true, labels: {{ color: '#a0a6b0' }} }}
                    }},
                    scales: {{
                        x: {{
                            ticks: {{ color: '#a0a6b0' }},
                            grid: {{ color: 'rgba(107, 207, 255, 0.1)' }},
                        }}
                    }}
                }}
            }});
        }}

        // Segmentation - Donut Chart
        function initSegmentationChart() {{
            const canvasId = 'segmentation-donut';
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;

            const segments = segmentationData.segments || [];
            const labels = segments.map(s => s.segment_name);
            const data = Array(labels.length).fill(20);  // Equal distribution for demo

            const colors = ['#00ff88', '#6bcfff', '#ffd93d', '#ff6b6b', '#00ddff'];

            const ctx = canvas.getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: labels,
                    datasets: [{{
                        data: data,
                        backgroundColor: colors.slice(0, labels.length),
                        borderColor: '#131a2b',
                        borderWidth: 2,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: true, position: 'bottom', labels: {{ color: '#a0a6b0' }} }}
                    }}
                }}
            }});
        }}

        // Pipeline Flow - RTQL Progression
        function initPipelineFlow() {{
            const canvasId = 'pipeline-rtql-progression';
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;

            const rtqlData = dashboardData.scenarios.map(s => s.l3.rtql_stage);
            const ctx = canvas.getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: dashboardData.scenarios.map(s => s.l1.prospect_name),
                    datasets: [{{
                        label: 'RTQL Stage (1-7)',
                        data: rtqlData,
                        backgroundColor: rtqlData.map(v => {{
                            if (v <= 2) return '#ff6b6b';
                            if (v <= 4) return '#ffd93d';
                            return '#00ff88';
                        }}),
                        borderColor: rtqlData.map(v => {{
                            if (v <= 2) return '#ff6b6b';
                            if (v <= 4) return '#ffd93d';
                            return '#00ff88';
                        }}),
                        borderWidth: 2,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        x: {{
                            min: 0, max: 7,
                            ticks: {{ color: '#a0a6b0' }},
                            grid: {{ color: 'rgba(107, 207, 255, 0.1)' }},
                        }},
                        y: {{
                            ticks: {{ color: '#a0a6b0' }},
                            grid: {{ color: 'rgba(107, 207, 255, 0.1)' }},
                        }}
                    }}
                }}
            }});
        }}

        // Card collapse/expand functionality
        document.querySelectorAll('.card-header').forEach(header => {{
            header.addEventListener('click', () => {{
                header.closest('.card').classList.toggle('collapsed');
            }});
        }});

        // Scenario tab switching
        document.querySelectorAll('.scenario-tab').forEach(tab => {{
            tab.addEventListener('click', () => {{
                const tabGroup = tab.closest('[data-tab-group]');
                if (!tabGroup) return;

                tabGroup.querySelectorAll('.scenario-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                const scenarioNum = tab.dataset.scenario;
                tabGroup.querySelectorAll('.scenario-content').forEach(content => {{
                    content.classList.remove('active');
                }});
                const activeContent = tabGroup.querySelector(`.scenario-content[data-scenario="${{scenarioNum}}"]`);
                if (activeContent) activeContent.classList.add('active');
            }});
        }});

        // Initialize first scenario tabs as active
        document.querySelectorAll('[data-tab-group]').forEach(group => {{
            const firstTab = group.querySelector('.scenario-tab');
            if (firstTab) {{
                firstTab.classList.add('active');
                const scenarioNum = firstTab.dataset.scenario;
                const content = group.querySelector(`.scenario-content[data-scenario="${{scenarioNum}}"]`);
                if (content) content.classList.add('active');
            }}
        }});

        // ─── NIX Modal Logic ────────────────────────────────────
        function openNixModal(scenarioNum) {{
            const modal = document.getElementById(`nix-modal-${{scenarioNum}}`);
            if (modal) {{
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }}
        }}

        function closeNixModal(scenarioNum) {{
            const modal = document.getElementById(`nix-modal-${{scenarioNum}}`);
            if (modal) {{
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }}
        }}

        // Close modal on overlay click
        document.querySelectorAll('.nix-modal-overlay').forEach(overlay => {{
            overlay.addEventListener('click', (e) => {{
                if (e.target === overlay) {{
                    overlay.classList.remove('active');
                    document.body.style.overflow = '';
                }}
            }});
        }});

        // Close on Escape
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                document.querySelectorAll('.nix-modal-overlay.active').forEach(m => {{
                    m.classList.remove('active');
                }});
                document.body.style.overflow = '';
            }}
        }});

        // Approve channel
        function approveChannel(scenarioNum, channelName) {{
            const btn = document.getElementById(`approve-${{scenarioNum}}-${{channelName}}`);
            if (btn) {{
                if (btn.classList.contains('approved')) {{
                    btn.classList.remove('approved');
                    btn.textContent = 'Approve This Channel';
                }} else {{
                    // Remove approval from other channels in same scenario
                    document.querySelectorAll(`[id^="approve-${{scenarioNum}}-"]`).forEach(b => {{
                        b.classList.remove('approved');
                        b.textContent = 'Approve This Channel';
                    }});
                    btn.classList.add('approved');
                    btn.textContent = 'Approved';
                }}
            }}
        }}
    </script>
</body>
</html>
"""

    return html


def _format_scenarios_for_js(scenarios: list) -> str:
    """Format scenarios data as JSON for JavaScript."""
    import json
    return json.dumps(scenarios)


def _format_segments_for_js(segments: list) -> str:
    """Format segmentation data as JSON for JavaScript."""
    import json
    return json.dumps(segments)


def _format_summary_for_js(summary: dict) -> str:
    """Format summary data as JSON for JavaScript."""
    import json
    return json.dumps(summary)


def _render_panel_executive_summary(summary: Dict[str, Any]) -> str:
    """Render Panel 1: Executive Summary."""
    verdicts = summary.get("verdicts_distribution", {})
    layer_statuses = summary.get("layer_statuses", {})

    verdict_html = "".join([
        f'<div class="verdict-badge {verdict}">{verdict.replace("_", " ").title()}: {count}</div>'
        for verdict, count in verdicts.items()
    ])

    layer_badges = "".join([
        f'<span class="status-badge healthy">{layer.upper()}: {status.title()}</span>'
        for layer, status in layer_statuses.items()
    ])

    return f"""
    <div class="card">
        <div class="card-header">
            <h2>Executive Summary</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <div class="metric">
                <span class="metric-label">Pipeline Health</span>
                <span class="metric-value">{summary.get("total_prospects", 0)} Prospects Scored</span>
            </div>

            <div style="margin-bottom: 16px;">
                <p style="color: #a0a6b0; margin-bottom: 8px; font-size: 0.9rem;">Verdict Distribution</p>
                {verdict_html}
            </div>

            <div class="metric">
                <span class="metric-label">Avg Prospect Fit</span>
                <span class="metric-value">{summary.get("avg_fit_score", 0)}/100</span>
            </div>
            <div class="metric">
                <span class="metric-label">Avg Value Score</span>
                <span class="metric-value">{summary.get("avg_value_score", 0):.3f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Avg Trust Score</span>
                <span class="metric-value">{summary.get("avg_trust_score", 0):.3f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Total Compensation Pool</span>
                <span class="metric-value">${summary.get("total_compensation_pool", 0):,.2f}</span>
            </div>

            <div style="margin-top: 16px;">
                <p style="color: #a0a6b0; margin-bottom: 8px; font-size: 0.9rem;">Layer Status</p>
                {layer_badges}
            </div>
        </div>
    </div>
    """


def _render_panel_l1_sensing(scenarios: list) -> str:
    """Render Panel 2: L1 Prospect Sensing."""
    scenario_tabs = "".join([
        f'<div class="scenario-tab" data-scenario="{s["scenario_num"]}">{s["scenario_num"]}: {s["scenario_name"][:30]}...</div>'
        for s in scenarios
    ])

    scenario_contents = "".join([
        f"""
        <div class="scenario-content" data-scenario="{s["scenario_num"]}">
            <h3 style="color: #6bcfff; margin-bottom: 12px;">{s["l1"]["prospect_name"]}</h3>
            <div style="height: 350px; margin-bottom: 20px;">
                <canvas id="l1-radar-{s["scenario_num"]-1}"></canvas>
            </div>
            <table>
                <tr><th>Component</th><th>Score</th></tr>
                <tr><td>Need</td><td>{s["l1"]["need"]}/100</td></tr>
                <tr><td>Service Fit</td><td>{s["l1"]["service_fit"]}/100</td></tr>
                <tr><td>Readiness</td><td>{s["l1"]["readiness"]}/100</td></tr>
                <tr><td>Accessibility</td><td>{s["l1"]["accessibility"]}/100</td></tr>
                <tr><td>Expected Uplift</td><td>{s["l1"]["expected_uplift"]}/100</td></tr>
                <tr><td>Economic Scale</td><td>{s["l1"]["economic_scale"]}/100</td></tr>
                <tr><td>Confidence</td><td>{s["l1"]["confidence"]}/100</td></tr>
                <tr style="background: rgba(107, 207, 255, 0.1);"><td><strong>Total Fit Score</strong></td><td><strong>{s["l1"]["total_fit_score"]}/100</strong></td></tr>
            </table>
            {"<p class='gap-pattern'><strong>Priority Gaps:</strong> " + ", ".join(s["l1"]["priority_gaps"]) + "</p>" if s["l1"]["priority_gaps"] else ""}
        </div>
        """
        for s in scenarios
    ])

    return f"""
    <div class="card">
        <div class="card-header">
            <h2>L1 — Prospect Sensing</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <div class="scenario-tabs" data-tab-group="l1">
                {scenario_tabs}
            </div>
            {scenario_contents}
        </div>
    </div>
    """


def _render_panel_l2_brand_experience(scenarios: list) -> str:
    """Render Panel 3: L2 Brand Experience."""
    scenario_tabs = "".join([
        f'<div class="scenario-tab" data-scenario="{s["scenario_num"]}">{s["scenario_num"]}: Scenario</div>'
        for s in scenarios
    ])

    scenario_contents = "".join([
        f"""
        <div class="scenario-content" data-scenario="{s["scenario_num"]}">
            <div style="height: 350px; margin-bottom: 20px;">
                <canvas id="l2-ethos-{s["scenario_num"]-1}"></canvas>
            </div>
            <div class="metric">
                <span class="metric-label">Coherence Composite</span>
                <span class="metric-value">{s["l2"]["coherence"]["composite_score"]}/100</span>
            </div>
            <div class="metric">
                <span class="metric-label">Ethos Coefficient</span>
                <span class="metric-value">{s["l2"]["coherence"]["coefficient"]:.3f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Channel Consistency</span>
                <span class="metric-value">{s["l2"]["channel_consistency_score"]}/100</span>
            </div>
            <div class="metric">
                <span class="metric-label">Proof-to-Promise Ratio</span>
                <span class="metric-value">{s["l2"]["proof_to_promise_ratio"]:.2%}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Trust Layer Quality</span>
                <span class="metric-value">{s["l2"]["trust_layer_quality"]}/100</span>
            </div>
            <div class="metric">
                <span class="metric-label">Brand Experience Score</span>
                <span class="metric-value">{s["l2"]["brand_experience_score"]}/100</span>
            </div>
        </div>
        """
        for s in scenarios
    ])

    return f"""
    <div class="card">
        <div class="card-header">
            <h2>L2 — Brand Experience</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <div class="scenario-tabs" data-tab-group="l2">
                {scenario_tabs}
            </div>
            {scenario_contents}
        </div>
    </div>
    """


def _render_panel_l3_qualification(scenarios: list) -> str:
    """Render Panel 4: L3 Qualification Engine."""
    scenario_tabs = "".join([
        f'<div class="scenario-tab" data-scenario="{s["scenario_num"]}">{s["scenario_num"]}: {s["l1"]["prospect_name"]}</div>'
        for s in scenarios
    ])

    scenario_contents = "".join([
        f"""
        <div class="scenario-content" data-scenario="{s["scenario_num"]}">
            <div style="margin-bottom: 16px;">
                <span class="verdict-badge {s["l3"]["verdict"]}">{s["l3"]["verdict"].upper()}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Value Score</span>
                <span class="metric-value">{s["l3"]["value_score"]:.3f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Trust Score</span>
                <span class="metric-value">{s["l3"]["trust_score"]:.3f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">RTQL Stage</span>
                <span class="metric-value">{s["l3"]["rtql_stage"]}/7</span>
            </div>
            <div class="metric">
                <span class="metric-label">RTQL Multiplier</span>
                <span class="metric-value">{s["l3"]["rtql_multiplier"]:.2f}x</span>
            </div>
            <div class="metric">
                <span class="metric-label">Priority Score</span>
                <span class="metric-value">{s["l3"]["priority_score"]:.3f}</span>
            </div>
            <div style="margin-top: 12px;">
                <p style="color: #a0a6b0; margin-bottom: 8px; font-size: 0.9rem;">Certificates</p>
                {"".join([f'<span class="certificate {"unchecked" if not v else ""}">{k.upper()}</span>' for k, v in s["l3"]["certificates"].items()])}
            </div>
            {"<div class='gap-pattern'><strong>Blocking Gates:</strong> " + ", ".join(s["l3"]["blocking_gates"]) + "</div>" if s["l3"]["blocking_gates"] else ""}
        </div>
        """
        for s in scenarios
    ])

    return f"""
    <div class="card">
        <div class="card-header">
            <h2>L3 — Qualification Engine</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <div style="height: 350px; margin-bottom: 20px;">
                <canvas id="l3-value-trust-scatter"></canvas>
            </div>
            <div class="scenario-tabs" data-tab-group="l3">
                {scenario_tabs}
            </div>
            {scenario_contents}
            <div style="height: 300px; margin-top: 20px;">
                <canvas id="pipeline-rtql-progression"></canvas>
            </div>
        </div>
    </div>
    """


def _render_panel_l4_execution(scenarios: list) -> str:
    """Render Panel 5: L4 Execution Matrix."""
    scenario_tabs = "".join([
        f'<div class="scenario-tab" data-scenario="{s["scenario_num"]}">{s["scenario_num"]}: {s["l1"]["prospect_name"]}</div>'
        for s in scenarios
    ])

    scenario_contents = "".join([
        f"""
        <div class="scenario-content" data-scenario="{s["scenario_num"]}">
            <div class="metric">
                <span class="metric-label">Total Interactions</span>
                <span class="metric-value">{s["l4"]["interaction_count"]}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Total Compensation</span>
                <span class="metric-value">${s["l4"]["total_compensation"]:,.2f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Avg NOCS</span>
                <span class="metric-value">{s["l4"]["avg_nocs"]:.2f}</span>
            </div>
            <table style="margin-top: 16px;">
                <tr><th>Interaction</th><th>Channel</th><th>NOCS</th><th>Compensation</th></tr>
                {"".join([f'<tr><td>{i["interaction_id"]}</td><td>{i["channel"]}</td><td>{i["nocs"]}</td><td>${i["compensation_total"]:.2f}</td></tr>' for i in s["l4"]["interactions"]])}
            </table>
        </div>
        """
        for s in scenarios
    ])

    return f"""
    <div class="card">
        <div class="card-header">
            <h2>L4 — Execution Matrix</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <div style="height: 300px; margin-bottom: 20px;">
                <canvas id="l4-compensation-waterfall"></canvas>
            </div>
            <div class="scenario-tabs" data-tab-group="l4">
                {scenario_tabs}
            </div>
            {scenario_contents}
        </div>
    </div>
    """


def _render_panel_segmentation(segmentation: dict) -> str:
    """Render Panel 6: Customer Segmentation."""
    segments = segmentation.get("segments", [])

    segment_rows = "".join([
        f"""
        <tr>
            <td><strong>{seg["segment_name"]}</strong></td>
            <td>{seg["primary_gap_pattern"]}</td>
            <td>${seg["expected_value_range"][0]}-${seg["expected_value_range"][1]}</td>
            <td>Tier {seg["priority_tier"]}</td>
        </tr>
        """
        for seg in segments
    ])

    return f"""
    <div class="card full-width">
        <div class="card-header">
            <h2>Customer Segmentation</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="height: 300px;">
                    <canvas id="segmentation-donut"></canvas>
                </div>
                <div>
                    <table style="font-size: 0.85rem;">
                        <tr><th>Segment</th><th>Gap Pattern</th><th>Expected Value</th><th>Tier</th></tr>
                        {segment_rows}
                    </table>
                </div>
            </div>
        </div>
    </div>
    """


def _render_panel_pipeline_flow(scenarios: list, summary: dict) -> str:
    """Render Panel 7: Pipeline Flow."""
    scenario_rows = "".join([
        f"""
        <tr>
            <td>{s["scenario_num"]}</td>
            <td>{s["l1"]["prospect_name"]}</td>
            <td>{s["l1"]["total_fit_score"]}</td>
            <td>{s["l3"]["value_score"]:.3f}</td>
            <td>{s["l3"]["trust_score"]:.3f}</td>
            <td><span class="verdict-badge {s["l3"]["verdict"]}" style="white-space: nowrap;">{s["l3"]["verdict"].replace("_", " ").title()}</span></td>
            <td>${s["l4"]["total_compensation"]:,.2f}</td>
        </tr>
        """
        for s in scenarios
    ])

    return f"""
    <div class="card full-width">
        <div class="card-header">
            <h2>Pipeline Flow — L1→L4 Progression</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <p style="color: #a0a6b0; margin-bottom: 16px; font-size: 0.9rem;">
                Complete pipeline results: prospect fit scores flow through qualification verdicts to execution compensation.
            </p>
            <table>
                <tr>
                    <th>#</th>
                    <th>Prospect</th>
                    <th>L1 Fit</th>
                    <th>L3 Value</th>
                    <th>L3 Trust</th>
                    <th>L3 Verdict</th>
                    <th>L4 Compensation</th>
                </tr>
                {scenario_rows}
            </table>
        </div>
    </div>
    """


def _render_panel_nix(scenarios: list) -> str:
    """Render Panel 8: Next Interaction Experience with View buttons."""
    scenario_cards = ""
    for s in scenarios:
        nix = s.get("nix", {})
        channels = nix.get("channels", [])
        top_channel = channels[0] if channels else {}
        intent = nix.get("primary_intent", "unknown")
        urgency = nix.get("urgency", "unknown")
        snum = s["scenario_num"]

        scenario_cards += f"""
        <div style="background: rgba(107, 207, 255, 0.05); border-radius: 10px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <strong style="color: #e0e6ed; font-size: 1.05rem;">{s["l1"]["prospect_name"]}</strong>
                    <span class="verdict-badge {nix.get('verdict', '')}" style="margin-left: 8px; font-size: 0.75rem; padding: 4px 10px;">{nix.get("verdict", "").replace("_", " ").upper()}</span>
                </div>
                <div>
                    <span class="nix-intent-badge {intent}">{intent.replace("_", " ").title()}</span>
                    <span class="nix-urgency-badge {urgency}">{urgency.replace("_", " ").title()}</span>
                </div>
            </div>
            <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="color: #a0a6b0; font-size: 0.85rem;">
                    Top Channel: <strong style="color: #00ff88;">{top_channel.get("channel", "N/A").replace("_", " ").title()}</strong>
                    (confidence: {top_channel.get("confidence", 0):.0%})
                    &mdash; Projected NOCS: <strong style="color: #6bcfff;">{top_channel.get("projected_nocs", 0):.1f}</strong>
                </div>
                <button class="nix-btn" onclick="openNixModal({snum})">
                    View Next Interaction <span class="arrow">&rarr;</span>
                </button>
            </div>
        </div>
        """

    return f"""
    <div class="card full-width">
        <div class="card-header">
            <h2>Next Interaction Experience</h2>
            <span class="card-toggle">▼</span>
        </div>
        <div class="card-content">
            <p style="color: #a0a6b0; margin-bottom: 16px; font-size: 0.9rem;">
                Recommended next interactions derived from L1-L4 pipeline state.
                Click <strong style="color: #00ff88;">View Next Interaction</strong> to see all channel recommendations and edit before execution.
            </p>
            {scenario_cards}
        </div>
    </div>
    """


def _render_nix_modals(scenarios: list) -> str:
    """Render NIX modal overlays for each scenario."""
    modals = ""
    for s in scenarios:
        nix = s.get("nix", {})
        snum = s["scenario_num"]
        channels = nix.get("channels", [])
        intent = nix.get("primary_intent", "unknown")
        urgency = nix.get("urgency", "unknown")

        # Strategy box
        strategy_html = f"""
        <div class="nix-strategy-box">
            <div class="label">Strategic Rationale</div>
            <p style="color: #e0e6ed; font-size: 0.95rem; margin-bottom: 10px;">{nix.get("strategic_rationale", "")}</p>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
                <span class="nix-intent-badge {intent}">Intent: {intent.replace("_", " ").title()}</span>
                <span class="nix-urgency-badge {urgency}">Urgency: {urgency.replace("_", " ").title()}</span>
            </div>
            <div style="display: flex; gap: 20px; color: #a0a6b0; font-size: 0.85rem;">
                <span>Fit: <strong style="color: #6bcfff;">{nix.get("current_fit_score", 0):.1f}</strong></span>
                <span>Value: <strong style="color: #6bcfff;">{nix.get("current_value_score", 0):.3f}</strong></span>
                <span>Trust: <strong style="color: #6bcfff;">{nix.get("current_trust_score", 0):.3f}</strong></span>
                <span>Target Trust Shift: <strong style="color: #00ff88;">+{nix.get("target_trust_shift", 0):.1f}</strong></span>
            </div>
        </div>
        """

        # Success criteria
        success_html = ""
        for crit in nix.get("success_criteria", []):
            success_html += f'<div class="nix-success-item">&#10003; {crit}</div>'

        # Blocking conditions
        blocking_html = ""
        for block in nix.get("blocking_conditions", []):
            blocking_html += f'<div class="nix-risk">&#9888; {block}</div>'

        # Prerequisites
        prereq_html = ""
        for prereq in nix.get("prerequisite_data", []):
            prereq_html += f'<div style="color: #ffd93d; font-size: 0.85rem; padding: 2px 0;">&#8226; {prereq}</div>'

        # Channel cards
        channels_html = ""
        for ch in channels[:6]:  # Show top 6 channels
            rank = ch.get("priority_rank", 99)
            rank_class = f"rank-{rank}" if rank <= 3 else ""
            channel_name = ch.get("channel", "unknown")
            confidence = ch.get("confidence", 0)
            conf_pct = confidence * 100
            conf_color = "#00ff88" if confidence > 0.7 else "#ffd93d" if confidence > 0.4 else "#ff6b6b"

            # Talking points
            tp_html = ""
            for tp in ch.get("key_talking_points", []):
                tp_html += f"<li>{tp}</li>"

            # Ethos targets mini display
            ethos_html = ""
            for dim, val in ch.get("ethos_targets", {}).items():
                short_dim = dim.replace("_", " ").replace("explainability", "expl.").replace("technology", "tech")
                ethos_html += f'<div class="nix-ethos-item"><span class="dim">{short_dim}</span><span class="val">{val:.0f}</span></div>'

            # Risk factors
            risk_html = ""
            for risk in ch.get("risk_factors", []):
                risk_html += f'<div class="nix-risk">&#9888; {risk}</div>'

            channels_html += f"""
            <div class="nix-channel-card {rank_class}">
                {"<div class='rank-badge'>#" + str(rank) + "</div>" if rank <= 3 else ""}
                <div class="nix-channel-name">{channel_name.replace("_", " ").title()}</div>
                <div style="color: #a0a6b0; font-size: 0.8rem; margin-bottom: 4px;">
                    Confidence: {confidence:.0%} &mdash; Projected NOCS: {ch.get("projected_nocs", 0):.1f} &mdash; ~{ch.get("estimated_duration_minutes", 0)} min
                </div>
                <div class="nix-confidence-bar">
                    <div class="nix-confidence-fill" style="width: {conf_pct}%; background: {conf_color};"></div>
                </div>

                <div style="color: #a0a6b0; font-size: 0.85rem; margin-bottom: 8px;">{ch.get("reasoning", "")}</div>

                <div class="nix-editable">
                    <div class="edit-label"><span class="edit-icon">&#9998;</span> Message Frame</div>
                    <textarea rows="3" id="msg-{snum}-{channel_name}">{ch.get("suggested_message_frame", "")}</textarea>
                </div>

                <div class="nix-editable">
                    <div class="edit-label"><span class="edit-icon">&#9998;</span> Tone</div>
                    <input type="text" id="tone-{snum}-{channel_name}" value="{ch.get("suggested_tone", "")}">
                </div>

                <div style="margin: 8px 0;">
                    <div style="color: #6bcfff; font-size: 0.8rem; margin-bottom: 4px;">KEY TALKING POINTS</div>
                    <ul class="nix-talking-points" style="padding-left: 16px; margin: 0;">
                        {tp_html}
                    </ul>
                </div>

                <div style="margin: 8px 0;">
                    <div style="color: #ffd93d; font-size: 0.8rem; margin-bottom: 4px;">ETHOS TARGETS</div>
                    <div class="nix-ethos-mini">{ethos_html}</div>
                </div>

                {f'<div style="margin: 8px 0;">{risk_html}</div>' if risk_html else ""}

                <div class="nix-editable">
                    <div class="edit-label"><span class="edit-icon">&#9998;</span> Operator Notes</div>
                    <textarea rows="2" id="notes-{snum}-{channel_name}" placeholder="Add notes before approving..."></textarea>
                </div>

                <button class="nix-approve-btn" id="approve-{snum}-{channel_name}" onclick="approveChannel({snum}, '{channel_name}')">
                    Approve This Channel
                </button>
            </div>
            """

        modals += f"""
        <div class="nix-modal-overlay" id="nix-modal-{snum}">
            <div class="nix-modal">
                <button class="nix-modal-close" onclick="closeNixModal({snum})">&#10005; Close</button>

                <div class="nix-header">
                    <h2>Next Interaction — {s["l1"]["prospect_name"]}</h2>
                    <p style="color: #a0a6b0;">Scenario {snum}: {s.get("scenario_name", "")}</p>
                </div>

                {strategy_html}

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <div style="color: #6bcfff; font-size: 0.85rem; margin-bottom: 6px; font-weight: bold;">SUCCESS CRITERIA</div>
                        {success_html}
                    </div>
                    <div>
                        {f'<div style="color: #ff6b6b; font-size: 0.85rem; margin-bottom: 6px; font-weight: bold;">BLOCKING CONDITIONS</div>{blocking_html}' if blocking_html else ""}
                        {f'<div style="color: #ffd93d; font-size: 0.85rem; margin-bottom: 6px; font-weight: bold;">PREREQUISITES</div>{prereq_html}' if prereq_html else ""}
                    </div>
                </div>

                <h3 style="color: #6bcfff; margin-bottom: 16px;">Channel Recommendations (All Channels)</h3>
                <div class="nix-channels-grid">
                    {channels_html}
                </div>
            </div>
        </div>
        """

    return modals
