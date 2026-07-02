from core.validator import normalize_reliability, validate_output, validate_schema


def test_validate_schema_fills_missing_keys():
    result = validate_schema({}, "variant")
    assert result == {
        "metadata": {},
        "variant_a": {},
        "variant_b": {},
        "variant_c": {},
    }


def test_validate_schema_keeps_existing_values():
    result = validate_schema({"variant_a": {"hook": "already here"}}, "variant")
    assert result["variant_a"] == {"hook": "already here"}
    assert result["variant_b"] == {}


def test_validate_schema_unknown_schema_is_a_no_op():
    data = {"anything": 1}
    assert validate_schema(data, "not_a_real_schema") == {"anything": 1}


def test_normalize_reliability_clamps_out_of_range_values():
    data = {"reliability": 5.0, "nested": {"reliability": -3.0}}
    normalize_reliability(data)
    assert data["reliability"] == 1.0
    assert data["nested"]["reliability"] == 0.0


def test_normalize_reliability_handles_non_numeric_values():
    data = {"reliability": "not-a-number"}
    normalize_reliability(data)
    assert data["reliability"] == 0.0


def test_normalize_reliability_recurses_into_lists():
    data = {"items": [{"reliability": 2.0}, {"reliability": 0.5}]}
    normalize_reliability(data)
    assert data["items"][0]["reliability"] == 1.0
    assert data["items"][1]["reliability"] == 0.5


def test_validate_output_runs_both_steps():
    data = {"metadata": {"reliability": 42}}
    result = validate_output(data, "variant")
    assert result["metadata"]["reliability"] == 1.0
    assert result["variant_a"] == {}
