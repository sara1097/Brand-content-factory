"""Offline tests for the Magic Hour editor -> generator fallback (no API calls)."""

import tools.magichour_client as mc


def _patch_happy_path(monkeypatch):
    monkeypatch.setattr(
        mc, "_wait_for_image",
        lambda project_id: {"status": "complete", "downloads": [{"url": "http://x/y.png"}]},
    )
    monkeypatch.setattr(mc, "_download_image", lambda url, dest: str(dest))


def test_editor_402_falls_back_to_text_only(monkeypatch):
    calls = []

    def fake_submit(prompt, reference_file_path, name, aspect_ratio):
        calls.append((prompt, reference_file_path))
        if reference_file_path:
            raise mc.MagicHourClientError("out of credits (402)")
        return {"id": "job1", "credits_charged": 5}

    monkeypatch.setattr(mc, "_submit_image_job", fake_submit)
    _patch_happy_path(monkeypatch)

    result = mc.generate_image(
        "a prompt",
        reference_file_path="api-assets/x/ref.jpg",
        fallback_prompt="a prompt plus exact product description",
    )

    # Editor tried first with the plain prompt, then text-only with the
    # enriched fallback prompt.
    assert calls == [
        ("a prompt", "api-assets/x/ref.jpg"),
        ("a prompt plus exact product description", None),
    ]
    assert result["status"] == "succeeded"
    assert result["reference_used"] is False
    assert result["prompt"] == "a prompt plus exact product description"


def test_reference_submission_success_keeps_reference(monkeypatch):
    monkeypatch.setattr(
        mc, "_submit_image_job",
        lambda prompt, reference_file_path, name, aspect_ratio: {"id": "job2", "credits_charged": 25},
    )
    _patch_happy_path(monkeypatch)

    result = mc.generate_image("a prompt", reference_file_path="api-assets/x/ref.jpg")
    assert result["status"] == "succeeded"
    assert result["reference_used"] is True


def test_text_only_submission_failure_is_reported_not_retried(monkeypatch):
    calls = []

    def fake_submit(prompt, reference_file_path, name, aspect_ratio):
        calls.append(reference_file_path)
        raise mc.MagicHourClientError("boom")

    monkeypatch.setattr(mc, "_submit_image_job", fake_submit)

    result = mc.generate_image("a prompt", reference_file_path=None)
    assert result["status"] == "failed"
    assert "boom" in result["error"]
    assert calls == [None]  # no second attempt without a reference to drop
