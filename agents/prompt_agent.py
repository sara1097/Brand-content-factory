import json

from models.llm import ask_qwen
from schemas.scene_prompt_schema import ScenePrompt, ScenePrompts
from schemas.storyboard_schema import Storyboard
from utils.json_parser import parse_json_response

def generate_scene_prompts(
    storyboard: Storyboard
) -> ScenePrompts:
    """Kept for backward compatibility with the old storyboard-based flow.
    Not used by agents/video_agent.py anymore -- see generate_video_prompts
    below for the current two-distinct-prompts / two-video flow."""

    prompt = f"""
You are an expert prompt engineer for Wan2.1.

Convert the storyboard into cinematic video prompts.

Return JSON matching this schema:

{json.dumps(ScenePrompts.model_json_schema(), indent=2)}

Storyboard:

{storyboard.model_dump_json(indent=2)}
"""

    response = ask_qwen(prompt)

    raw_prompts = parse_json_response(response)

    # prompts = [
    #     ScenePrompt(**item)
    #     for item in raw_prompts
    # ]
    prompts = ScenePrompts.model_validate(raw_prompts)
    return prompts


def _condense(data: dict | None, max_chars: int = 800) -> dict:
    """Bounds how much marketing/content JSON gets embedded in the prompt
    instruction, so a large marketing/content payload can't blow the
    request's token budget."""
    if not data:
        return {}
    text = json.dumps(data, ensure_ascii=False)
    if len(text) <= max_chars:
        return data
    return {"summary": text[:max_chars] + "...(truncated)"}


def generate_video_prompts(
    description: str,
    product: dict | None = None,
    marketing: dict | None = None,
    content: dict | None = None,
    model: str | None = None,
    num_prompts: int = 2,
) -> list[str]:
    """
    Turns the user's raw product description + product/marketing/content
    intelligence into `num_prompts` (default 2) DISTINCT, enhanced,
    cinematic WanGP video prompts -- different creative directions for the
    same product, enhanced/rewritten by Qwen. Each prompt is rendered as
    its own separate video by agents/video_agent.py (two different videos,
    not the same prompt reused with different seeds). No storyboard /
    multi-scene split.
    """
    product = product or {}

    branding_facts = {
        "product_name": product.get("product_name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "colors": product.get("colors"),
        "materials": product.get("materials"),
        "visible_text": product.get("visible_text"),
        "visible_logos": product.get("visible_logos"),
    }

    instruction = f"""
You are an expert prompt engineer for the WanGP / LTX-2 text-to-video model.

Write {num_prompts} DIFFERENT, detailed, cinematic video-generation
prompts for the SAME product -- {num_prompts} distinct creative
directions (e.g. different camera move, mood, setting, or focal detail).
Do not just reword the same idea; each prompt must describe a genuinely
different take.

Rules for EACH prompt:
- ONE continuous single shot / camera move only (e.g. slow orbit, push-in,
  pan). Do NOT write multiple scenes, a shot list, or numbered steps.
- If product_name, brand, visible_text or visible_logos below are not
  empty, add a short "STRICT REQUIREMENT" clause telling the model to keep
  that exact branding/text/logo unchanged.
- Commercial / advertisement style. Mention lighting, surface/setting, and
  camera behaviour.
- Reflect the marketing strategy and content plan below where relevant
  (target audience, campaign goal/tone, platform), if they are not empty.
- 2 to 4 sentences long, plain prose (no bullet points, no markdown).

Return ONLY this JSON object, nothing else, no markdown fences:
{{"video_prompts": [{", ".join(f'"<prompt {i + 1}>"' for i in range(num_prompts))}]}}

User's product description:
{description}

Known product facts (may be partially empty -- ignore empty ones):
{json.dumps(branding_facts, indent=2, ensure_ascii=False)}

Marketing strategy context (may be empty -- ignore if empty):
{json.dumps(_condense(marketing), indent=2, ensure_ascii=False)}

Content calendar context (may be empty -- ignore if empty):
{json.dumps(_condense(content), indent=2, ensure_ascii=False)}
"""

    response = ask_qwen(instruction, model=model)
    parsed = parse_json_response(response)

    raw_prompts = parsed.get("video_prompts") if isinstance(parsed, dict) else None
    cleaned = (
        [str(p).strip() for p in raw_prompts if str(p).strip()]
        if isinstance(raw_prompts, list)
        else []
    )

    if len(cleaned) >= num_prompts:
        return cleaned[:num_prompts]

    # Never return fewer than num_prompts, even if Qwen's JSON didn't come
    # back with enough distinct entries -- pad with clearly-labeled
    # alternate takes derived from what we do have (or the raw description).
    base = cleaned[0] if cleaned else description.strip()
    padded = list(cleaned)
    while len(padded) < num_prompts:
        variant_index = len(padded) + 1
        padded.append(
            f"{base} Alternate take {variant_index}: different camera angle, "
            "framing and mood, same product and branding."
        )
    return padded