"""Advanced Analytics & Insights Agent"""
import json
from datetime import datetime


def generate_detailed_report(product_data: dict, market_research: dict, research_history: list = None) -> dict:
    """Generate comprehensive detailed report"""
    
    system_prompt = """You are a professional market research report analyst.
Create detailed, professional, and actionable reports.
ALWAYS respond with valid JSON only."""
    
    history_context = ""
    if research_history:
        history_context = f"\n\nHistorical Data:\n{json.dumps(research_history[-3:], ensure_ascii=False)}"
    
    user_prompt = f"""Generate comprehensive market research report:

Product: {json.dumps(product_data, indent=2, ensure_ascii=False)}

Market Research: {json.dumps(market_research, indent=2, ensure_ascii=False)}
{history_context}

Return JSON with this EXACT structure:

{{
  "executive_summary": "2-3 paragraph executive summary",
  "key_findings": [
    "finding1 with specific data",
    "finding2 with specific data",
    "finding3 with specific data"
  ],
  "market_analysis": {{
    "market_size": "estimated market size",
    "growth_rate": "growth percentage/trend",
    "dominant_players": ["player1", "player2"],
    "market_gaps": "opportunities identified"
  }},
  "competitor_analysis": {{
    "main_competitors": ["comp1", "comp2"],
    "our_positioning": "how this product stands out",
    "competitive_advantages": ["advantage1", "advantage2"],
    "competitive_threats": ["threat1", "threat2"]
  }},
  "consumer_insights": {{
    "target_audience": "detailed audience description",
    "buying_factors": ["factor1", "factor2", "factor3"],
    "pain_points": ["pain1", "pain2"],
    "value_drivers": ["value1", "value2"]
  }},
  "pricing_strategy": {{
    "current_price_point": "competitive analysis",
    "value_perception": "how market perceives value",
    "pricing_recommendations": "suggested pricing strategy",
    "discount_strategy": "seasonal/promotional recommendations"
  }},
  "action_items": [
    {{"priority": "high/medium/low", "action": "specific action", "impact": "expected impact"}},
    {{"priority": "high/medium/low", "action": "specific action", "impact": "expected impact"}}
  ],
  "risk_assessment": {{
    "market_risks": ["risk1", "risk2"],
    "mitigation_strategies": ["strategy1", "strategy2"],
    "opportunities": ["opportunity1", "opportunity2"]
  }},
  "forecast": {{
    "3_month_outlook": "forecast",
    "6_month_outlook": "forecast",
    "12_month_outlook": "forecast"
  }}
}}"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    raw_output = call_groq(messages, temperature=0.3)
    return parse_json_response(raw_output, retry_messages=messages)


def segment_market_analysis(category: str, product_data: dict) -> dict:
    """Analyze market segmentation and positioning"""
    
    system_prompt = """You are a market segmentation expert.
Provide detailed market segment analysis with specific data.
ALWAYS respond with valid JSON only."""
    
    user_prompt = f"""Analyze market segmentation for {category} category:

Product: {json.dumps(product_data, indent=2, ensure_ascii=False)}

Identify and analyze market segments in the Egyptian market.

Return JSON with this EXACT structure:

{{
  "market_segments": [
    {{
      "segment_name": "segment 1",
      "size_estimate": "% of market",
      "characteristics": "demographic and psychographic details",
      "buying_power": "purchasing capability",
      "preferences": ["preference1", "preference2"],
      "price_sensitivity": "high/medium/low",
      "channels_preferred": ["channel1", "channel2"]
    }},
    {{
      "segment_name": "segment 2",
      "size_estimate": "% of market",
      "characteristics": "demographic and psychographic details",
      "buying_power": "purchasing capability",
      "preferences": ["preference1", "preference2"],
      "price_sensitivity": "high/medium/low",
      "channels_preferred": ["channel1", "channel2"]
    }}
  ],
  "target_segment_recommendation": {{
    "segment": "recommended target segment",
    "reasons": ["reason1", "reason2"],
    "market_potential": "size and growth opportunity",
    "competitive_intensity": "how competitive is this segment"
  }},
  "niche_opportunities": [
    "opportunity1",
    "opportunity2",
    "opportunity3"
  ],
  "segment_messaging": {{
    "segment1": "tailored messaging",
    "segment2": "tailored messaging"
  }},
  "channel_strategy_by_segment": {{
    "segment1": ["channel1", "channel2"],
    "segment2": ["channel1", "channel2"]
  }}
}}"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    raw_output = call_groq(messages, temperature=0.35)
    return parse_json_response(raw_output, retry_messages=messages)


def get_ecommerce_insights(product_data: dict, market_research: dict) -> dict:
    """Specific e-commerce channel analysis"""
    
    system_prompt = """You are an e-commerce strategist for Egyptian market.
Provide practical e-commerce insights for platforms like Amazon Egypt, Noon, Jumia, etc.
ALWAYS respond with valid JSON only."""
    
    user_prompt = f"""Analyze e-commerce strategy for Egyptian market:

Product: {json.dumps(product_data, indent=2, ensure_ascii=False)}
Market Context: {json.dumps(market_research, indent=2, ensure_ascii=False)}

Return JSON with this EXACT structure:

{{
  "best_platforms": [
    {{"platform": "Jumia", "potential": "high/medium/low", "reasoning": "why suitable", "estimated_sales": "projection"}},
    {{"platform": "Noon", "potential": "high/medium/low", "reasoning": "why suitable", "estimated_sales": "projection"}}
  ],
  "marketplace_strategy": {{
    "product_title_optimization": "SEO-optimized title",
    "key_keywords": ["keyword1", "keyword2", "keyword3"],
    "category_placement": "best category path",
    "bullet_points": ["point1", "point2", "point3", "point4"],
    "description_strategy": "how to write compelling description"
  }},
  "pricing_strategy_ecommerce": {{
    "competitive_pricing": "price positioning",
    "promotional_calendar": "suggested promotions",
    "bundle_opportunities": "bundling suggestions"
  }},
  "logistics_considerations": {{
    "fulfillment_recommendation": "FBM vs FBA recommendation",
    "shipping_optimization": "logistics strategy",
    "returns_policy": "recommended policy"
  }},
  "customer_acquisition": {{
    "advertising_budget_allocation": "suggested ad spend distribution",
    "peak_seasons": ["season1", "season2"],
    "promotional_hooks": "what drives purchases"
  }},
  "review_strategy": {{
    "target_rating": "optimal rating to target",
    "review_generation_tactics": ["tactic1", "tactic2"],
    "negative_review_handling": "how to handle criticism"
  }},
  "social_commerce_opportunities": [
    {{"platform": "TikTok Shop", "strategy": "specific strategy"}},
    {{"platform": "Instagram Shopping", "strategy": "specific strategy"}},
    {{"platform": "Facebook Marketplace", "strategy": "specific strategy"}}
  ]
}}"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    raw_output = call_groq(messages, temperature=0.35)
    return parse_json_response(raw_output, retry_messages=messages)
