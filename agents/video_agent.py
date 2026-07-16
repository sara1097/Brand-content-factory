"""
Video generation agent.

Flow:
  1. Take the user's raw product description + optional analyzed product
     intelligence + optional marketing strategy + optional content plan +
     optional uploaded photo.
  2. Ask Qwen for TWO DISTINCT cinematic video prompts -- two different
     creative directions for the same product, grounded in the marketing
     strategy / content plan when available
     (agents.prompt_agent.generate_video_prompts).
  3. Render each prompt as its own separate video (two different prompts
     -> two different videos) through the deployed WanGP API
     (models.wangp_client).

No storyboard, no per-scene prompts, no video stitching, and the two
videos are not the same prompt reused with different seeds -- they come
from two distinct prompts.
"""
from agents.content_calendar import days_by_media_type
from agents.prompt_agent import generate_video_prompts
from config import QWEN_MODEL, WANGP_NUM_VARIANTS
from models.wangp_client import WanGPClientError, generate_video_variants


def generate_video_assets(
    description: str,
    product: dict | None = None,
    marketing: dict | None = None,
    content: dict | None = None,
    image_path: str | None = None,
    on_progress=None,
) -> dict:
    """
    Args:
        description: the raw product description the user typed in.
        product: optional product-intelligence dict from agents.product_agent
            (used to keep exact branding/text/logo consistent in the prompts).
        marketing: optional marketing-strategy dict (target audience,
            campaign goal, tone, etc.) -- folded into the prompt context.
        content: optional content-calendar dict -- folded into the prompt
            context.
        image_path: optional local path to the uploaded product photo. When
            given, it's sent to WanGP as an image reference on every video
            so the product's packaging/branding is preserved.
        on_progress: optional callback(variant, total_variants, pct, status,
            phase) invoked as each video's render progresses -- e.g. wire
            this up to a Streamlit progress bar. Never raises even if the
            callback itself errors.

    Returns a dict with the two distinct prompts and their generated video
    variants, e.g.:

        {
            "prompts": ["...", "..."],
            "image_used": True,
            "num_variants": 2,
            "variants": [
                {"variant": 1, "prompt": "...", "seed": 123, "job_id": "...",
                 "status": "succeeded", "video_path": "outputs/<id>.mp4"},
                {"variant": 2, "prompt": "...", "seed": 456, "job_id": "...",
                 "status": "succeeded", "video_path": "outputs/<id>.mp4"},
            ],
            "is_placeholder": False,
        }
    """
    if not description or not description.strip():
        return {"error": "A product description is required to generate a video."}

    # When the calendar declares video days (media_type == "video"), each
    # rendered video belongs to one of those days -- the prompts are
    # written from those posts and the variants are tagged with the day.
    video_days = days_by_media_type(content or {}, "video")[:WANGP_NUM_VARIANTS]
    day_numbers = [day.get("day") for day in video_days]

    try:
        prompts = generate_video_prompts(
            description=description,
            product=product,
            marketing=marketing,
            content=content,
            model=QWEN_MODEL,
            num_prompts=WANGP_NUM_VARIANTS,
        )

        print(f"\n[VideoAgent] Qwen generated {len(prompts)} distinct video prompt(s):")
        for i, prompt in enumerate(prompts, start=1):
            day_label = f" (day {day_numbers[i - 1]})" if i <= len(day_numbers) else ""
            print(f"[VideoAgent]   Prompt {i}{day_label}: {prompt}")

        variants = generate_video_variants(
            prompts=prompts,
            image_path=image_path,
            on_progress=on_progress,
        )
    except WanGPClientError as exc:
        return {"error": f"WanGP API error: {exc}"}
    except Exception as exc:
        return {"error": str(exc)}

    for i, variant in enumerate(variants):
        variant["day"] = day_numbers[i] if i < len(day_numbers) else None

    return {
        "prompts": prompts,
        "days": day_numbers,
        "image_used": bool(image_path),
        "num_variants": len(variants),
        "variants": variants,
        "is_placeholder": False,
    }