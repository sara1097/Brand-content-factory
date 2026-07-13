"""Offline tests for reference-image candidate scoring (no API calls)."""

from agents.image_validator_agent import score_candidate


def _verdict(confidence=0.8, quality=0.5, product_only=False, background="other"):
    return {
        "match": True,
        "confidence": confidence,
        "quality": quality,
        "product_only": product_only,
        "background": background,
    }


def test_clean_studio_shot_beats_cluttered_scene():
    clean = _verdict(confidence=0.8, quality=0.9, product_only=True, background="white")
    cluttered = _verdict(confidence=0.9, quality=0.4, product_only=False, background="other")
    assert score_candidate(clean) > score_candidate(cluttered)


def test_black_background_gets_same_bonus_as_white():
    white = _verdict(background="white")
    black = _verdict(background="black")
    other = _verdict(background="other")
    assert score_candidate(white) == score_candidate(black)
    assert score_candidate(white) > score_candidate(other)


def test_product_only_is_preferred():
    solo = _verdict(product_only=True)
    busy = _verdict(product_only=False)
    assert score_candidate(solo) > score_candidate(busy)


def test_quality_breaks_ties():
    sharp = _verdict(quality=0.9)
    noisy = _verdict(quality=0.3)
    assert score_candidate(sharp) > score_candidate(noisy)
