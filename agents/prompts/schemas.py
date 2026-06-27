"""schemas.py
Shared output schemas for all AI agents.
"""
import json

# ============================================================
# BASE BLOCKS
# ============================================================

INTELLIGENCE_BLOCK = {
    "attributes": {},
    "assessment": {},
    "evidence": [],
    "reliability": 0.0
}

# ============================================================
# PRODUCT SCHEMA
# ============================================================

PRODUCT_SCHEMA = {
    "metadata": {
        "agent": "product_intelligence",
        "schema_version": "1.0.0",
        "status": "success"
    },
    "identity_intelligence": {
        "attributes": {
            "product_name": "",
            "brand": "",
            "category": "",
            "subcategory": "",
            "product_type": ""
        },
        "assessment": {"identification_quality": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "visual_intelligence": {
        "attributes": {
            "dominant_colors": [],
            "secondary_colors": [],
            "shape": "",
            "surface_finish": "",
            "design_language": "",
            "style": "",
            "branding_visibility": ""
        },
        "assessment": {
            "overall_design_quality": "",
            "visual_score": 0
        },
        "evidence": [],
        "reliability": 0.0
    },
    "construction_intelligence": {
        "attributes": {
            "estimated_materials": [],
            "build_quality": "",
            "manufacturing_quality": "",
            "durability_estimation": "",
            "manufacturing_complexity": ""
        },
        "assessment": {"overall_build_score": 0},
        "evidence": [],
        "reliability": 0.0
    },
    "feature_intelligence": {
        "attributes": [
            {
                "name": "",
                "description": "",
                "importance": "",
                "visibility": ""
            }
        ],
        "assessment": {"feature_completeness": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "quality_intelligence": {
        "attributes": {
            "visual_strengths": [],
            "visual_weaknesses": [],
            "premium_indicators": [],
            "budget_indicators": [],
            "visible_defects": []
        },
        "assessment": {"overall_quality": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "limitations": {
        "missing_information": [],
        "uncertain_information": [],
        "visibility_constraints": []
    }
}

# ============================================================
# RESEARCH SCHEMA
# ============================================================

RESEARCH_SCHEMA = {
    "metadata": {
        "agent": "market_intelligence",
        "schema_version": "1.0.0",
        "status": "success"
    },
    "market_intelligence": {
        "attributes": {
            "market_size": "",
            "market_growth": "",
            "market_maturity": "",
            "trend_direction": "",
            "seasonality": ""
        },
        "assessment": {
            "market_attractiveness": "",
            "growth_potential": ""
        },
        "evidence": {"price_sources": [], "market_sources": []},
        "reliability": 0.0
    },
    "competitive_intelligence": {
        "attributes": {
            "direct_competitors": [],
            "indirect_competitors": [],
            "market_leaders": [],
            "market_gap": ""
        },
        "assessment": {
            "competition_level": "",
            "competitive_pressure": ""
        },
        "evidence": {"competitor_sources": []},
        "reliability": 0.0
    },
    "pricing_intelligence": {
        "attributes": {
            "price_range": "",
            "average_price": "",
            "budget_segment": "",
            "mid_segment": "",
            "premium_segment": ""
        },
        "assessment": {
            "pricing_strategy": "",
            "price_position": ""
        },
        "evidence": {"price_sources": []},
        "reliability": 0.0
    },
    "consumer_intelligence": {
        "attributes": {
            "target_segments": [],
            "customer_personas": [],
            "pain_points": [],
            "motivations": [],
            "buying_behavior": []
        },
        "assessment": {
            "purchase_intent": "",
            "market_fit": ""
        },
        "evidence": {"review_sources": []},
        "reliability": 0.0
    },
    "channel_intelligence": {
        "attributes": {
            "offline_channels": [],
            "online_channels": [],
            "marketplaces": [],
            "recommended_channels": []
        },
        "assessment": {"best_channel": ""},
        "evidence": {"distribution_sources": []},
        "reliability": 0.0
    },
    "trend_intelligence": {
        "attributes": {
            "emerging_trends": [],
            "declining_trends": [],
            "opportunities": [],
            "threats": []
        },
        "assessment": {"future_outlook": ""},
        "evidence": {"trend_sources": []},
        "reliability": 0.0
    },
    "limitations": {
        "missing_information": [],
        "uncertain_information": [],
        "search_limitations": []
    }
}

# ============================================================
# MARKETING SCHEMA
# ============================================================

MARKETING_SCHEMA = {
    "metadata": {
        "agent": "marketing_strategy",
        "schema_version": "1.0.0",
        "status": "success"
    },
    "executive_strategy": {
        "attributes": {
            "business_goal": "",
            "marketing_goal": "",
            "success_definition": "",
            "strategic_priority": ""
        },
        "assessment": {
            "overall_strategy_strength": "",
            "market_readiness": ""
        },
        "evidence": [],
        "reliability": 0.0
    },
    "stp_analysis": {
        "attributes": {
            "segmentation": [],
            "target_audience": [],
            "positioning_statement": "",
            "value_proposition": ""
        },
        "assessment": {"target_market_fit": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "swot_analysis": {
        "attributes": {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        },
        "assessment": {"competitive_position": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "pricing_strategy": {
        "attributes": {
            "pricing_model": "",
            "recommended_price_range": "",
            "pricing_position": "",
            "discount_strategy": "",
            "bundling_strategy": ""
        },
        "assessment": {"pricing_competitiveness": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "go_to_market_strategy": {
        "attributes": {
            "launch_strategy": "",
            "market_entry_plan": "",
            "customer_acquisition_strategy": "",
            "retention_strategy": ""
        },
        "assessment": {"execution_feasibility": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "channel_strategy": {
        "attributes": {
            "offline_channels": [],
            "online_channels": [],
            "marketplaces": [],
            "social_platforms": [],
            "recommended_channel_mix": ""
        },
        "assessment": {"channel_effectiveness": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "content_strategy": {
        "attributes": {
            "brand_message": "",
            "brand_voice": "",
            "content_pillars": [],
            "content_formats": [],
            "storytelling_angle": ""
        },
        "assessment": {"engagement_potential": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "campaign_strategy": {
        "attributes": {
            "launch_campaign": "",
            "seasonal_campaigns": [],
            "campaign_ideas": [],
            "promotional_tactics": [],
            "call_to_actions": []
        },
        "assessment": {"campaign_strength": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "budget_strategy": {
        "attributes": {
            "digital_budget_percentage": "",
            "offline_budget_percentage": "",
            "estimated_budget_level": "",
            "budget_allocation": []
        },
        "assessment": {"budget_efficiency": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "kpi_framework": {
        "attributes": {
            "primary_kpis": [],
            "secondary_kpis": [],
            "success_metrics": [],
            "reporting_frequency": ""
        },
        "assessment": {"measurement_quality": ""},
        "evidence": [],
        "reliability": 0.0
    },
    "risk_management": {
        "attributes": {
            "business_risks": [],
            "marketing_risks": [],
            "competitive_risks": [],
            "mitigation_actions": []
        },
        "assessment": {"overall_risk_level": ""},
        "evidence": [],
        "reliability": 0.0
    }
}

# ============================================================
# REPORT SCHEMA
# ============================================================

REPORT_SCHEMA = {
    "metadata": {
        "agent": "executive_report",
        "schema_version": "1.0.0",
        "status": "success"
    },
    "executive_summary": {
        "overview": "",
        "key_findings": [],
        "business_outlook": "",
        "confidence": 0.0
    },
    "product_assessment": {
        "summary": "",
        "strengths": [],
        "weaknesses": [],
        "overall_quality": ""
    },
    "market_assessment": {
        "summary": "",
        "market_size": "",
        "competition_level": "",
        "pricing_position": "",
        "consumer_behavior": ""
    },
    "marketing_assessment": {
        "summary": "",
        "positioning": "",
        "go_to_market": "",
        "channels": [],
        "campaigns": []
    },
    "swot_summary": {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": []
    },
    "strategic_recommendations": {
        "immediate_actions": [],
        "mid_term_actions": [],
        "long_term_actions": []
    },
    "implementation_roadmap": {
        "phase_1": [],
        "phase_2": [],
        "phase_3": []
    },
    "kpi_framework": {
        "business_kpis": [],
        "marketing_kpis": [],
        "financial_kpis": []
    },
    "executive_verdict": {
        "decision": "",
        "business_readiness": "",
        "risk_level": "",
        "final_recommendation": ""
    }
}

# ============================================================
# JSON EXPORTS
# ============================================================

PRODUCT_SCHEMA_JSON = json.dumps(PRODUCT_SCHEMA, indent=4, ensure_ascii=False)
RESEARCH_SCHEMA_JSON = json.dumps(RESEARCH_SCHEMA, indent=4, ensure_ascii=False)
MARKETING_SCHEMA_JSON = json.dumps(MARKETING_SCHEMA, indent=4, ensure_ascii=False)
REPORT_SCHEMA_JSON = json.dumps(REPORT_SCHEMA, indent=4, ensure_ascii=False)