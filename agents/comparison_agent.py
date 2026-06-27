"""Comparison & Recommendation Agent"""
import json


def compare_products(product_list: list) -> dict:
    """Compare multiple products and provide analysis"""
    
    system_prompt = """You are an expert product comparison analyst.
Compare products comprehensively and objectively.
ALWAYS respond with valid JSON only - no markdown."""
    
    user_prompt = f"""Compare these {len(product_list)} products in detail:

{json.dumps(product_list, indent=2, ensure_ascii=False)}

Return JSON with this EXACT structure:

{{
  "comparison_summary": "2-3 sentence summary of the comparison",
  "best_overall": {{
    "product": "product name",
    "reason": "why it's best overall"
  }},
  "best_value": {{
    "product": "product name",
    "reason": "best price-to-quality ratio"
  }},
  "best_premium": {{
    "product": "product name",
    "reason": "best premium option"
  }},
  "feature_comparison": {{
    "feature1": {{"product1": "rating", "product2": "rating"}},
    "feature2": {{"product1": "rating", "product2": "rating"}}
  }},
  "recommendation": "detailed recommendation based on use case",
  "pros_cons": {{
    "product1": {{"pros": ["pro1", "pro2"], "cons": ["con1", "con2"]}},
    "product2": {{"pros": ["pro1", "pro2"], "cons": ["con1", "con2"]}}
  }}
}}"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    raw_output = call_groq(messages, temperature=0.3)
    return parse_json_response(raw_output, retry_messages=messages)


def get_recommendations(product_data: dict, use_case: str, budget: str = None) -> dict:
    """Get personalized recommendations based on use case"""
    
    system_prompt = """You are an expert shopping advisor for Egyptian market.
Provide personalized, practical recommendations based on use case and preferences.
ALWAYS respond with valid JSON only."""
    
    budget_str = f"\nBudget: {budget} EGP" if budget else ""
    
    user_prompt = f"""Provide personalized recommendations:

Product: {json.dumps(product_data, indent=2, ensure_ascii=False)}
Use Case: {use_case}
{budget_str}

Return JSON with this EXACT structure:

{{
  "recommendation": "personalized buying recommendation",
  "best_places_to_buy": ["store1", "store2", "platform3"],
  "price_tracking_tips": "tips for getting best price",
  "alternatives": [
    {{"name": "alternative1", "reason": "why consider this", "approx_price": "EGP range"}},
    {{"name": "alternative2", "reason": "why consider this", "approx_price": "EGP range"}}
  ],
  "buying_tips": ["tip1", "tip2", "tip3"],
  "warranty_check": "information about warranty in Egypt",
  "user_reviews_synthesis": "summary of what Egyptian users think"
}}"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    raw_output = call_groq(messages, temperature=0.4)
    return parse_json_response(raw_output, retry_messages=messages)


def analyze_trend(category: str, product_list: list = None) -> dict:
    """Analyze market trends for a category"""
    
    system_prompt = """You are a market trend analyst.
Analyze trends in Egyptian consumer market.
ALWAYS respond with valid JSON only."""
    
    products_context = ""
    if product_list:
        products_context = f"\nRecent products analyzed in this category:\n{json.dumps(product_list, ensure_ascii=False)}"
    
    user_prompt = f"""Analyze current market trends for {category} in Egypt:{products_context}

Return JSON with this EXACT structure:

{{
  "trend_direction": "increasing/decreasing/stable",
  "trend_reasons": ["reason1", "reason2", "reason3"],
  "growth_forecast": "forecast for next 3-6 months",
  "consumer_sentiment": "positive/negative/mixed",
  "market_drivers": ["driver1", "driver2"],
  "competitive_landscape": "description of competition",
  "price_trajectory": "whether prices are going up or down and why",
  "emerging_alternatives": ["new tech/product type 1", "new option 2"],
  "buy_timing_advice": "best time to buy recommendation"
}}"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    raw_output = call_groq(messages, temperature=0.3)
    return parse_json_response(raw_output, retry_messages=messages)
