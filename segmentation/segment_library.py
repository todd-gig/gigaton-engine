"""Predefined customer segments for the Gigaton Engine.

Segments now include L2 brand coherence and L4 interaction performance
qualifying criteria alongside L1 prospect attributes. When brand_assessment
or interaction_context is not provided to SegmentationEngine.classify(),
L2/L4 criteria are simply skipped (graceful degradation).
"""

from segmentation.models.segment import CustomerSegment
from segmentation.models.segment_criteria import ApolloTargeting


# Predefined segment definitions based on gap patterns, maturity levels,
# brand coherence, and interaction performance
SEGMENT_LIBRARY = {
    "high_growth_low_infrastructure": CustomerSegment(
        segment_id="SEG_001",
        segment_name="High Growth / Low Infrastructure",
        description="Fast-growing companies with strong product-market fit but immature marketing/measurement infrastructure. Strong brand experience but weak conversion architecture.",
        qualifying_criteria={
            "economic_scale": (60, 100),
            "marketing_maturity": ("low", "medium"),
            "measurement_maturity": ("low",),
            "gtm_motion": ("sales_led", "hybrid"),
            "fit_score": (50, 100),
        },
        # L2: When brand data available, this segment expects decent brand scores
        # (these companies have good product-market fit, so brand should be present)
        brand_criteria={
            "brand_experience_score": (40, 100),
        },
        # L4: When interaction data available, expect active engagement
        interaction_criteria={
            "interaction_conversion_rate": (0.0, 1.0),  # Any conversion acceptable
        },
        service_package_fit=[
            "Brand experience engineering",
            "Measurement infrastructure",
            "Interaction management system",
            "Analytics instrumentation",
        ],
        expected_value_range=(65, 95),
        priority_tier=1,
        primary_gap_pattern="strong traffic / weak conversion architecture",
        apollo_targeting=ApolloTargeting(
            industries=["saas", "technology", "software"],
            employee_count_ranges=["51-200", "201-500", "501-1000"],
            revenue_ranges=["$10M-$50M", "$50M-$100M"],
            technologies=["Google Analytics", "HubSpot", "Salesforce"],
            titles=["VP Marketing", "CMO", "Director of Marketing", "Head of Growth"],
            seniority_levels=["director", "vp", "c_suite"],
            departments=["marketing", "growth"],
            locations=["United States", "Canada"],
            keywords=["B2B SaaS", "growth stage", "series B", "series C"],
        ),
    ),
    "enterprise_trust_gap": CustomerSegment(
        segment_id="SEG_002",
        segment_name="Enterprise / Trust Layer Gap",
        description="Large enterprises with clear sales-led motion but poor trust/proof infrastructure. Low proof-to-promise ratio and weak trust layer quality.",
        qualifying_criteria={
            "economic_scale": (70, 100),
            "sales_complexity": ("high",),
            "marketing_maturity": ("medium", "high"),
            "measurement_maturity": ("low", "medium"),
            "gtm_motion": ("sales_led",),
            "fit_score": (40, 100),
        },
        # L2: Trust gap is the defining characteristic — low proof, low trust quality
        brand_criteria={
            "proof_to_promise_ratio": (0.0, 0.65),  # Low proof vs claims
            "trust_layer_quality": (0, 60),           # Weak trust infrastructure
        },
        # L4: These companies are engaging but escalations signal trust issues
        interaction_criteria={
            "interaction_escalation_rate": (0.0, 0.5),  # Some escalations expected
        },
        service_package_fit=[
            "Brand architecture",
            "Trust layer engineering",
            "Case study development",
            "Sales enablement",
        ],
        expected_value_range=(55, 85),
        priority_tier=1,
        primary_gap_pattern="clear enterprise motion / poor trust layer",
        apollo_targeting=ApolloTargeting(
            industries=["technology", "financial services", "healthcare", "manufacturing"],
            employee_count_ranges=["501-1000", "1001-5000", "5001-10000"],
            revenue_ranges=["$50M-$100M", "$100M-$500M"],
            technologies=["Salesforce", "Marketo", "Eloqua"],
            titles=["VP Marketing", "CMO", "VP Sales", "CRO"],
            seniority_levels=["vp", "c_suite"],
            departments=["marketing", "sales"],
            locations=["United States"],
            keywords=["enterprise", "B2B", "complex sales"],
        ),
    ),
    "content_rich_measurement_poor": CustomerSegment(
        segment_id="SEG_003",
        segment_name="Content-Rich / Measurement-Poor",
        description="Companies investing heavily in content but lacking analytics and attribution. Good brand coherence but conversion performance gap.",
        qualifying_criteria={
            "economic_scale": (40, 80),
            "marketing_maturity": ("medium",),
            "measurement_maturity": ("low",),
            "fit_score": (35, 80),
        },
        # L2: Brand coherence is decent (they invest in content) but conversion lags
        brand_criteria={
            "brand_coherence_composite": (45, 100),    # Reasonable brand foundation
            "brand_conversion_performance": (0.0, 0.5),  # Weak conversion vs target
        },
        interaction_criteria={},
        service_package_fit=[
            "Analytics instrumentation",
            "Attribution modeling",
            "Performance measurement",
            "Dashboarding",
        ],
        expected_value_range=(45, 75),
        priority_tier=2,
        primary_gap_pattern="heavy content / weak analytics instrumentation",
        apollo_targeting=ApolloTargeting(
            industries=["technology", "media", "education", "professional services"],
            employee_count_ranges=["51-200", "201-500"],
            revenue_ranges=["$5M-$10M", "$10M-$50M"],
            technologies=["WordPress", "HubSpot", "Google Analytics"],
            titles=["Director of Marketing", "Content Director", "VP Marketing"],
            seniority_levels=["director", "vp"],
            departments=["marketing", "content"],
            locations=["United States", "Canada", "United Kingdom"],
            keywords=["content marketing", "inbound", "thought leadership"],
        ),
    ),
    "plg_conversion_friction": CustomerSegment(
        segment_id="SEG_004",
        segment_name="PLG / Conversion Friction",
        description="Product-led companies with public pricing but weak CTA/form strategy and conversion architecture. Channel consistency issues signal fragmented user experience.",
        qualifying_criteria={
            "gtm_motion": ("plg", "hybrid"),
            "marketing_maturity": ("low", "medium"),
            "economic_scale": (30, 70),
            "fit_score": (30, 70),
        },
        # L2: Low channel consistency signals fragmented PLG experience
        brand_criteria={
            "channel_consistency": (0, 75),  # Inconsistent channels = conversion friction
        },
        # L4: High abandonment rate signals conversion friction
        interaction_criteria={
            "interaction_abandonment_rate": (0.05, 1.0),  # Notable abandonment
        },
        service_package_fit=[
            "CRO",
            "Conversion architecture",
            "Lifecycle automation",
            "Onboarding optimization",
        ],
        expected_value_range=(35, 65),
        priority_tier=2,
        primary_gap_pattern="public pricing / weak CTA and form strategy",
        apollo_targeting=ApolloTargeting(
            industries=["saas", "software", "developer tools"],
            employee_count_ranges=["11-50", "51-200"],
            revenue_ranges=["$1M-$5M", "$5M-$10M"],
            technologies=["Stripe", "Intercom", "Segment"],
            titles=["Head of Growth", "VP Product", "Director of Marketing"],
            seniority_levels=["manager", "director", "vp"],
            departments=["growth", "marketing", "product"],
            locations=["United States", "Canada"],
            keywords=["PLG", "product-led", "self-serve", "freemium"],
        ),
    ),
    "brand_narrative_sales_gap": CustomerSegment(
        segment_id="SEG_005",
        segment_name="Brand Narrative / Sales Enablement Gap",
        description="Strong brand narrative but weak sales enablement and interaction consistency. Brand coherence high but interaction effectiveness low.",
        qualifying_criteria={
            "sales_complexity": ("high",),
            "marketing_maturity": ("medium", "high"),
            "interaction_management_maturity": ("low",),
            "fit_score": (40, 85),
        },
        # L2: Strong brand (that's the "narrative" part) but ethos isn't translating
        brand_criteria={
            "brand_coherence_composite": (55, 100),  # Good brand foundation exists
        },
        # L4: Low interaction effectiveness signals enablement gap
        interaction_criteria={
            "interaction_sentiment": (0.0, 0.6),       # Low sentiment signals disconnect
            "interaction_trust_shift": (-1.0, 0.1),    # Trust not growing from interactions
        },
        service_package_fit=[
            "Sales enablement",
            "Interaction management system",
            "RevOps cleanup",
            "Lifecycle automation",
        ],
        expected_value_range=(50, 80),
        priority_tier=2,
        primary_gap_pattern="strong brand narrative / weak sales enablement",
        apollo_targeting=ApolloTargeting(
            industries=["technology", "professional services", "consulting", "financial services"],
            employee_count_ranges=["201-500", "501-1000"],
            revenue_ranges=["$10M-$50M", "$50M-$100M"],
            technologies=["Salesforce", "HubSpot", "Gong", "Outreach"],
            titles=["VP Sales", "CRO", "VP Marketing", "Director of Sales Enablement"],
            seniority_levels=["director", "vp", "c_suite"],
            departments=["sales", "marketing", "revenue operations"],
            locations=["United States"],
            keywords=["B2B", "sales enablement", "revenue operations"],
        ),
    ),
}
