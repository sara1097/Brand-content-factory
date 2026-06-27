"""Deterministic profitability calculations (no LLM guesses)."""
from __future__ import annotations

from statistics import median


def market_price_stats(evidence: dict) -> dict:
    prices = [
        float(item["price_egp"])
        for item in evidence.get("price_sources", [])
        if item.get("price_egp")
    ]
    if not prices:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": len(prices),
        "min": round(min(prices), 2),
        "median": round(median(prices), 2),
        "max": round(max(prices), 2),
    }


def calculate_profitability(
    product_cost: float,
    selling_price: float,
    shipping_cost: float = 0,
    packaging_cost: float = 0,
    platform_fee_percent: float = 0,
    ads_percent: float = 0,
    other_cost: float = 0,
    target_margin_percent: float = 25,
) -> dict:
    product_cost = max(0.0, float(product_cost))
    selling_price = max(0.0, float(selling_price))
    fixed_costs = product_cost + shipping_cost + packaging_cost + other_cost
    variable_rate = max(0.0, platform_fee_percent + ads_percent) / 100
    variable_costs = selling_price * variable_rate
    total_cost = fixed_costs + variable_costs
    net_profit = selling_price - total_cost
    margin = (net_profit / selling_price * 100) if selling_price else 0
    roi = (net_profit / total_cost * 100) if total_cost else 0

    target_margin = max(0.0, min(float(target_margin_percent), 95.0)) / 100
    denominator = 1 - variable_rate - target_margin
    recommended_price = fixed_costs / denominator if denominator > 0 else None
    break_even_price = fixed_costs / (1 - variable_rate) if variable_rate < 1 else None

    return {
        "selling_price": round(selling_price, 2),
        "fixed_costs": round(fixed_costs, 2),
        "variable_costs": round(variable_costs, 2),
        "total_cost": round(total_cost, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin_percent": round(margin, 2),
        "roi_percent": round(roi, 2),
        "break_even_price": round(break_even_price, 2) if break_even_price else None,
        "recommended_price": round(recommended_price, 2) if recommended_price else None,
        "target_margin_percent": round(target_margin * 100, 2),
        "is_profitable": net_profit > 0,
    }
