"""Offline tests for the per-day variant loop with anti-repetition memory."""

import graph.nodes as gn


def _content(n_days=3):
    return {"days": [
        {"day": i, "platform": "instagram", "post_idea": f"Idea {i}", "media_type": "image"}
        for i in range(1, n_days + 1)
    ]}


def test_previous_hooks_accumulate_across_days(monkeypatch):
    calls = []

    def fake_generate_variants(marketing, content, model=None, settings_overrides=None,
                               previous_hooks=None, previous_ctas=None):
        day = content["days"][0]["day"]
        calls.append({"day": day, "hooks_seen": list(previous_hooks), "ctas_seen": list(previous_ctas)})
        return {
            "variant_a": {"hook": f"H{day}a", "cta": f"C{day}a"},
            "variant_b": {"hook": f"H{day}b", "cta": f"C{day}b"},
            "variant_c": {"hook": f"H{day}c", "cta": f"C{day}c"},
        }

    monkeypatch.setattr(gn, "generate_variants", fake_generate_variants)

    state = {"marketing": {"x": 1}, "content": _content(3)}
    result = gn.variants_node(state, None)["variants"]

    assert len(result["days"]) == 3
    assert result["metadata"]["status"] == "success"
    # Day 1 sees nothing; day 2 sees day 1's hooks; day 3 sees days 1+2.
    assert calls[0]["hooks_seen"] == []
    assert calls[1]["hooks_seen"] == ["H1a", "H1b", "H1c"]
    assert calls[2]["hooks_seen"] == ["H1a", "H1b", "H1c", "H2a", "H2b", "H2c"]
    assert calls[2]["ctas_seen"][-1] == "C2c"


def test_one_failed_day_does_not_kill_the_node(monkeypatch):
    def fake_generate_variants(marketing, content, **kwargs):
        day = content["days"][0]["day"]
        if day == 2:
            return {"error": "boom"}
        return {"variant_a": {"hook": f"H{day}", "cta": f"C{day}"},
                "variant_b": {}, "variant_c": {}}

    monkeypatch.setattr(gn, "generate_variants", fake_generate_variants)

    result = gn.variants_node({"marketing": {"x": 1}, "content": _content(3)}, None)["variants"]
    assert "node_error" not in result
    assert result["days"][1]["error"] == "boom"
    assert "variants" in result["days"][0] and "variants" in result["days"][2]


def test_all_days_failing_marks_node_error(monkeypatch):
    monkeypatch.setattr(gn, "generate_variants", lambda *a, **k: {"error": "boom"})
    result = gn.variants_node({"marketing": {"x": 1}, "content": _content(2)}, None)["variants"]
    assert "node_error" in result


def test_compliance_reviews_every_day(monkeypatch):
    reviewed = []

    def fake_generate_compliance(marketing, variants, model=None, settings_overrides=None):
        reviewed.append(variants["variant_a"]["hook"])
        return {"variant_a": {"safe_campaign_text": {"hook": variants["variant_a"]["hook"]}}}

    monkeypatch.setattr(gn, "generate_compliance", fake_generate_compliance)

    state = {"marketing": {"x": 1}, "variants": {"days": [
        {"day": 1, "topic": "T1", "variants": {"variant_a": {"hook": "H1"}}},
        {"day": 2, "topic": "T2", "error": "variant generation failed"},
        {"day": 3, "topic": "T3", "variants": {"variant_a": {"hook": "H3"}}},
    ]}}

    result = gn.compliance_node(state, None)["compliance"]

    assert reviewed == ["H1", "H3"]  # every day with variants got its own review
    assert result["metadata"]["reviewed_days"] == 2
    assert result["days"][0]["compliance"]
    assert "error" in result["days"][1]  # failed variant day carried through
    assert result["days"][2]["day"] == 3


def test_compliance_single_shot_shape_keeps_old_behavior(monkeypatch):
    calls = []
    monkeypatch.setattr(
        gn, "generate_compliance",
        lambda marketing, variants, **k: calls.append(variants) or {"ok": True},
    )
    state = {"marketing": {"x": 1}, "variants": {"variant_a": {"hook": "X"}}}
    result = gn.compliance_node(state, None)["compliance"]
    assert result == {"ok": True}
    assert calls == [{"variant_a": {"hook": "X"}}]


def test_compliance_all_days_failing_marks_node_error(monkeypatch):
    monkeypatch.setattr(gn, "generate_compliance", lambda *a, **k: {"error": "boom"})
    state = {"marketing": {"x": 1}, "variants": {"days": [
        {"day": 1, "variants": {"variant_a": {"hook": "H1"}}},
    ]}}
    result = gn.compliance_node(state, None)["compliance"]
    assert "node_error" in result
