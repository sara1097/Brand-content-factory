"""Offline tests for the final 7-day plan assembly node (no API key needed)."""

from graph.nodes import assemble_calendar_node


def _content():
    return {
        "campaign_name": "Launch Week",
        "days": [
            {"day": 1, "media_type": "video", "post_idea": "Teaser"},
            {"day": 2, "media_type": "image", "post_idea": "Feature close-up"},
            {"day": 3, "media_type": "text", "post_idea": "Poll"},
            {"day": 4, "media_type": "image", "post_idea": "Lifestyle"},
            {"day": 5, "media_type": "video", "post_idea": "Demo"},
            {"day": 6, "media_type": "image", "post_idea": "Testimonial"},
            {"day": 7, "media_type": "image", "post_idea": "Offer"},
        ],
    }


def test_media_paths_are_attached_per_day():
    state = {
        "content": _content(),
        "video": {"variants": [
            {"day": 1, "status": "succeeded", "video_path": "outputs/v1.mp4", "prompt": "p1"},
            {"day": 5, "status": "succeeded", "video_path": "outputs/v5.mp4", "prompt": "p5"},
        ]},
        "images": {"images": [
            {"day": 2, "status": "succeeded", "image_path": "outputs/images/i2.png", "prompt": "q2"},
            {"day": 4, "status": "failed", "error": "boom", "prompt": "q4"},
            {"day": 6, "status": "succeeded", "image_path": "outputs/images/i6.png", "prompt": "q6"},
            {"day": 7, "status": "succeeded", "image_path": "outputs/images/i7.png", "prompt": "q7"},
        ]},
    }

    final = assemble_calendar_node(state, None)["final_calendar"]
    days = {d["day"]: d for d in final["days"]}

    assert final["campaign_name"] == "Launch Week"
    assert final["media_mix"] == {"video": 2, "image": 4, "text": 1}

    assert days[1]["media_path"] == "outputs/v1.mp4"
    assert days[5]["media_status"] == "succeeded"
    assert days[2]["media_path"] == "outputs/images/i2.png"
    assert days[4]["media_status"] == "failed"
    assert days[4]["media_error"] == "boom"
    assert days[3]["media_status"] == "not_required"
    assert days[3]["media_path"] is None


def test_missing_media_is_marked_not_dropped():
    state = {"content": _content(), "video": {}, "images": {}}
    final = assemble_calendar_node(state, None)["final_calendar"]
    assert len(final["days"]) == 7
    statuses = {d["day"]: d["media_status"] for d in final["days"]}
    assert statuses[1] == "missing" and statuses[2] == "missing"
    assert statuses[3] == "not_required"


def test_errored_calendar_yields_node_error():
    state = {"content": {"node_error": "boom"}, "video": {}, "images": {}}
    final = assemble_calendar_node(state, None)["final_calendar"]
    assert "node_error" in final


def test_extra_caption_prefers_compliance_safe_text():
    state = {
        "content": _content(),
        "video": {}, "images": {},
        "variants": {"days": [
            {"day": 1, "variants": {"variant_a": {"hook": "raw hook 1", "body": "b", "cta": "c"}}},
            {"day": 2, "variants": {"variant_a": {"hook": "raw hook 2", "body": "b", "cta": "c"}}},
        ]},
        "compliance": {"days": [
            {"day": 1, "compliance": {"variant_a": {"safe_campaign_text": {
                "hook": "safe hook 1", "body": "safe body", "cta": "safe cta"}}}},
            {"day": 2, "error": "review failed"},
        ]},
    }

    final = assemble_calendar_node(state, None)["final_calendar"]
    days = {d["day"]: d for d in final["days"]}

    # Day 1: compliance-safe text wins over the raw variant.
    assert days[1]["extra_caption"]["hook"] == "safe hook 1"
    assert days[1]["extra_caption"]["source"] == "compliance_safe"
    # Day 2: compliance failed -> falls back to the raw variant A.
    assert days[2]["extra_caption"]["hook"] == "raw hook 2"
    assert days[2]["extra_caption"]["source"] == "variant"
    # Day 3: no variants at all -> no extra caption key.
    assert "extra_caption" not in days[3]
