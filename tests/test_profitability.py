from tools.profitability import calculate_profitability, market_price_stats


def test_market_price_stats_with_no_prices():
    assert market_price_stats({"price_sources": []}) == {
        "count": 0,
        "min": None,
        "median": None,
        "max": None,
    }


def test_market_price_stats_computes_min_median_max():
    evidence = {
        "price_sources": [
            {"price_egp": 100},
            {"price_egp": None},  # should be ignored
            {"price_egp": 300},
            {"price_egp": 200},
        ]
    }
    stats = market_price_stats(evidence)
    assert stats == {"count": 3, "min": 100.0, "median": 200.0, "max": 300.0}


def test_calculate_profitability_basic_scenario():
    result = calculate_profitability(
        product_cost=1000,
        selling_price=1600,
        shipping_cost=70,
        packaging_cost=30,
        platform_fee_percent=10,
        ads_percent=8,
        other_cost=0,
        target_margin_percent=25,
    )
    assert result["fixed_costs"] == 1100.0
    assert result["variable_costs"] == 288.0  # 18% of 1600
    assert result["total_cost"] == 1388.0
    assert result["net_profit"] == 212.0
    assert result["is_profitable"] is True


def test_calculate_profitability_zero_selling_price_does_not_raise():
    result = calculate_profitability(product_cost=100, selling_price=0)
    assert result["profit_margin_percent"] == 0
    assert result["is_profitable"] is False


def test_calculate_profitability_full_variable_rate_has_no_break_even():
    result = calculate_profitability(
        product_cost=100,
        selling_price=200,
        platform_fee_percent=60,
        ads_percent=40,  # variable_rate == 1.0
    )
    assert result["break_even_price"] is None


def test_calculate_profitability_clamps_target_margin_to_95_percent():
    result = calculate_profitability(
        product_cost=100,
        selling_price=200,
        target_margin_percent=500,
    )
    assert result["target_margin_percent"] == 95.0
