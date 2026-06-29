from agents.content_calendar import generate_content_calendar

def build_content_strategy(marketing: dict) -> dict:
    return {
        "customer_personas": [
            {
                "name": "Target Audience",
                "target_audience": marketing.get("stp_analysis", {}).get("attributes", {}).get("target_audience", []),
                "pain_points": marketing.get("stp_analysis", {}).get("attributes", {}).get("pain_points", []),
                "motivations": marketing.get("stp_analysis", {}).get("attributes", {}).get("customer_motivations", [])
            }
        ],
        "marketing_angles": marketing.get("content_strategy", {}).get("attributes", {}).get("marketing_angles", []),
        "campaign_ideas": marketing.get("campaign_strategy", {}).get("attributes", {}).get("campaign_ideas", []),
        "customer_journey": marketing.get("go_to_market_strategy", {}).get("attributes", {}).get("customer_journey", {}),
        "swot": marketing.get("swot_analysis", {}).get("attributes", {}),
        "success_kpis": marketing.get("kpi_framework", {}).get("attributes", {}).get("success_metrics", [])
    }

def generate_content(marketing_strategy: dict) -> dict:
    strategy = build_content_strategy(marketing_strategy)

    campaign_name = (
        marketing_strategy
        .get("campaign_strategy", {})
        .get("attributes", {})
        .get("campaign_name", "Marketing Campaign")
    )

    return generate_content_calendar(strategy, campaign_name)