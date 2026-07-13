"""Offline tests for the 7-day media-mix enforcement (no API key needed)."""

from agents.content_calendar import (
    VIDEO_FORMATS,
    VISUAL_FORMATS,
    days_by_media_type,
    enforce_media_mix,
)
from config import MEDIA_MIX


def _make_day(day, media_type=None, content_format="static_post"):
    return {
        "day": day,
        "platform": "instagram",
        "media_type": media_type,
        "content_format": content_format,
        "post_idea": f"Idea {day}",
        "hook": f"Hook {day}",
        "caption": f"Caption {day}",
        "hashtags": ["#brand"],
        "cta": "Shop now",
        "visual_notes": "",
    }


def _mix_counts(calendar):
    return {
        media_type: len(days_by_media_type(calendar, media_type))
        for media_type in ("video", "image", "text")
    }


def test_correct_llm_output_is_preserved():
    calendar = {"days": [
        _make_day(1, "video", "reel"),
        _make_day(2, "image", "carousel"),
        _make_day(3, "image", "static_post"),
        _make_day(4, "text", "poll"),
        _make_day(5, "video", "tiktok"),
        _make_day(6, "image", "infographic"),
        _make_day(7, "image", "static_post"),
    ]}
    result = enforce_media_mix(calendar)
    assert _mix_counts(result) == MEDIA_MIX
    # Declared assignments respected as-is.
    assert [d["media_type"] for d in result["days"]] == [
        "video", "image", "image", "text", "video", "image", "image",
    ]


def test_missing_media_types_are_filled_to_exact_mix():
    calendar = {"days": [_make_day(i) for i in range(1, 8)]}
    result = enforce_media_mix(calendar)
    assert _mix_counts(result) == MEDIA_MIX


def test_llm_overshoot_is_corrected():
    # LLM said 7 video days -- only 2 may survive.
    calendar = {"days": [_make_day(i, "video", "reel") for i in range(1, 8)]}
    result = enforce_media_mix(calendar)
    assert _mix_counts(result) == MEDIA_MIX


def test_content_format_matches_media_type():
    calendar = {"days": [
        _make_day(1, "video", "poll"),          # video day with non-video format
        _make_day(2, "image", "reel"),          # image day with video format
        _make_day(3, "text", "youtube_short"),  # text day with video format
        _make_day(4, "image"),
        _make_day(5, "image"),
        _make_day(6, "video", "tiktok"),
        _make_day(7, "image"),
    ]}
    result = enforce_media_mix(calendar)
    for day in result["days"]:
        if day["media_type"] == "video":
            assert day["content_format"] in VIDEO_FORMATS
        elif day["media_type"] == "image":
            assert day["content_format"] in VISUAL_FORMATS | {"static_post"}
        else:
            assert day["content_format"] in {"poll", "static_post"}


def test_short_calendar_is_padded_to_seven_days():
    calendar = {"campaign_name": "Launch", "days": [_make_day(1), _make_day(2)]}
    result = enforce_media_mix(calendar)
    assert len(result["days"]) == 7
    assert _mix_counts(result) == MEDIA_MIX
    assert [d["day"] for d in result["days"]] == list(range(1, 8))


def test_long_calendar_is_truncated_to_seven_days():
    calendar = {"days": [_make_day(i) for i in range(1, 12)]}
    result = enforce_media_mix(calendar)
    assert len(result["days"]) == 7
    assert _mix_counts(result) == MEDIA_MIX


def test_media_days_get_visual_notes():
    calendar = {"days": [_make_day(i) for i in range(1, 8)]}
    result = enforce_media_mix(calendar)
    for day in result["days"]:
        if day["media_type"] in {"video", "image"}:
            assert day["visual_notes"]
