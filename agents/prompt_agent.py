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
    days: list[dict] | None = None,
    has_reference_image: bool = False,
) -> list[str]:
    """
    Turns the user's raw product description + product/marketing/content
    intelligence into `num_prompts` (default 2) DISTINCT, enhanced,
    cinematic WanGP video prompts -- different creative directions for the
    same product, enhanced/rewritten by Qwen. Each prompt is rendered as
    its own separate video by agents/video_agent.py (two different videos,
    not the same prompt reused with different seeds). No storyboard /
    multi-scene split.

    When `days` is given (the calendar's video-day posts), one prompt is
    written PER DAY, in order, grounded in that day's post_idea / hook /
    visual_notes / platform -- so each rendered video belongs to a
    specific day of the 7-day plan.
    """
    product = product or {}

    if days:
        num_prompts = len(days)

    branding_facts = {
        "product_name": product.get("product_name"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "colors": product.get("colors"),
        "materials": product.get("materials"),
        "visible_text": product.get("visible_text"),
        "visible_logos": product.get("visible_logos"),
    }

    reference_rule = ""
    if has_reference_image:
        reference_rule = """
- A reference photo of the product is provided to the video model
  alongside your prompt. State explicitly in each prompt that the
  product must appear EXACTLY as in the reference image -- same shape,
  colors, materials, packaging, branding and text -- no redesign."""

    day_briefs_section = ""
    if days:
        day_briefs = [
            {
                "day": day.get("day"),
                "platform": day.get("platform"),
                "post_idea": day.get("post_idea"),
                "hook": day.get("hook"),
                "visual_notes": day.get("visual_notes"),
            }
            for day in days
        ]
        day_briefs_section = f"""
Each video corresponds to one day of a 7-day content calendar (brief N
-> prompt N, in order). Use each brief ONLY as a hint for the video's
theme, mood, setting and platform. The video itself must STILL be a
product-hero advertisement: the physical product is the main subject of
every moment of the shot. Do NOT literally film what a brief describes
when it is not the product itself -- no people, testimonials, unboxing
hands, interviews, charts or text overlays. Translate the brief's idea
into camera movement, lighting, surface/setting and mood AROUND the
product:
{json.dumps(day_briefs, indent=2, ensure_ascii=False)}
"""

    instruction = f"""
You are an expert prompt engineer for the WanGP / LTX-2 text-to-video model.

Write {num_prompts} DIFFERENT, detailed, cinematic video-generation
prompts for the SAME product -- {num_prompts} distinct creative
directions. Do not just reword the same idea; each prompt must describe
a genuinely different take.
{day_briefs_section}
Creative directions (mandatory):
- Prompt 1 = PRODUCT FEATURES IN USE, BODY ANCHORED IN PLACE: the
  product stays anchored in one spot for the entire shot -- ZERO
  traveling, rolling, driving, sliding, floating or drifting across
  the scene. (Tilting or pivoting IN PLACE as part of real use -- a
  bottle tipping to pour -- is allowed.) Its features and parts
  operate one after another, as if someone is trying it out, AND when
  natural the shot also shows the satisfying RESULT of that use beside
  the product: a cheese pack's lid lifts off, revealing the cheese,
  with a fresh sandwich made with that cheese sitting beside the pack;
  a drink bottle's cap lifts, then it tips gently and pours into a
  clear glass that slowly fills; a TV screen lights up and plays a
  vivid colorful scene; a fridge door swings open revealing shelves
  stocked with fresh food; a toy car stays parked while its door
  swings open, then its headlights glow on; a perfume cap lifts, then
  one fine mist sprays. Pick the two or three feature interactions
  (plus their visible result) that best show off THIS specific
  product, happening ONE AFTER ANOTHER, never at the same time. For
  devices with screens, the screen shows a vivid cinematic scene or
  imagery ONLY -- never menus, interfaces, icons or on-screen text.
  The prompt must state explicitly that the product's body stays
  anchored in place while its features operate. CRITICAL: each motion stays
  SLOW, gentle and mechanically correct, with its direction stated
  explicitly (a door pivots outward on its hinge; a cap lifts straight
  up). Fast, jerky or simultaneous motion causes broken, physically
  wrong artifacts.
- Prompt 2 onwards = CINEMATIC REVEAL + ORBIT: the product is static
  and pristine in a REALISTIC, LIVING environment that fits it -- real
  surfaces and a believable setting with natural depth of field and
  subtle background life (drifting light, dust motes, soft out-of-focus
  movement). NEVER a plain, empty or abstract studio backdrop. The
  camera does NOT start framed on the product, but it starts CLOSE BY:
  just off to the side, on the same surface or a neighbouring object a
  hand's width away. From there it makes a SHORT, smooth glide onto the
  product, then smoothly moves around it (orbit / arc) as the hero
  reveal -- all within the single take. Do NOT start far away or travel
  across the room: long camera journeys through the scene cause broken
  geometry.
  CRITICAL -- REAL-WORLD SCALE: the product must appear at its TRUE
  physical size relative to the environment, and the prompt must state
  that size against a nearby object (e.g. a palm-sized toy car dwarfed
  by the bookshelf it sits on; a hand-sized perfume bottle small on the
  marble counter). The product must NEVER look oversized, room-sized or
  larger than the furniture around it.

Rules for EACH prompt:
- ONE continuous single take only -- no cuts, no multiple scenes, no
  shot lists, no numbered steps. A compound camera move inside the one
  take is fine (e.g. short glide onto the product, then orbit it).
- The product is the hero: it fills the frame through CLOSE-UP CAMERA
  FRAMING -- prominence comes from the camera being near the product,
  NEVER from the product being physically big. Keep it in sharp focus
  for the entire shot. No unrelated products. People or hands may
  appear ONLY when the product-in-action direction requires them (e.g.
  clothing being worn, a finger pressing a sprayer) -- partial, softly
  out of focus, never taking attention from the product.
- TRUE PHYSICAL SIZE, in EVERY prompt: state the product's real-world
  size class explicitly (palm-sized, hand-sized, a slim bracelet that
  fits a wrist, a bottle that fits in one hand...) AND anchor it
  against a nearby object in the scene (it occupies only a small
  corner of the table; it is smaller than the coffee mug beside it).
  The product must NEVER appear oversized relative to its
  surroundings -- a bracelet is a small piece of jewelry, not as wide
  as the table; a toy car is palm-sized, not furniture-sized.
- On-screen text policy: any text visible in the frame must be ENGLISH
  ONLY -- never Arabic or any other language/script, and never invented
  words or gibberish lettering. Do NOT invent brand names, labels or
  packaging text: the only brand text allowed is the product's own real
  branding, exactly as it really is. A short English promotional badge
  (e.g. "NEW", "LIMITED") is acceptable when the day's idea calls for
  one; otherwise keep the frame free of text. Say this explicitly in
  every prompt.
- If product_name, brand, visible_text or visible_logos below are not
  empty, add a short "STRICT REQUIREMENT" clause telling the model to
  keep the branding/text/logo printed ON the product unchanged -- never
  as separate graphics or overlays.{reference_rule}
- Commercial / advertisement style. Mention lighting, surface/setting, and
  camera behaviour.
- Reflect the marketing strategy and content plan below where relevant
  (target audience, campaign goal/tone, platform), if they are not empty.
- 2 to 4 sentences long, plain prose (no bullet points, no markdown).

Return ONLY this JSON object, nothing else, no markdown fences:
{{"video_prompts": [{", ".join(
    f'{{"direction": "{"action" if i == 0 else "hero"}", "prompt": "<prompt {i + 1}>"}}'
    for i in range(num_prompts)
)}]}}

User's product description:
{description}

Known product facts (may be partially empty -- ignore empty ones):
{json.dumps(branding_facts, indent=2, ensure_ascii=False)}

Marketing strategy context (may be empty -- ignore if empty):
{json.dumps(_condense(marketing), indent=2, ensure_ascii=False)}

Content calendar context (may be empty -- ignore if empty):
{json.dumps(_condense(content), indent=2, ensure_ascii=False)}
"""

    # Small output budget: 2 labeled prompts are ~400 tokens. The
    # instruction itself is long, and Groq's 6000 TPM limit counts
    # prompt + reserved completion tokens together -- the default 4000
    # reservation was what triggered 413 "Request too large".
    response = ask_qwen(instruction, model=model, max_completion_tokens=1200)
    parsed = parse_json_response(response)

    raw_prompts = parsed.get("video_prompts") if isinstance(parsed, dict) else None

    # Entries may be {"direction": ..., "prompt": ...} objects (current
    # schema) or plain strings (older model output). The product-in-action
    # prompt must always end up FIRST -- variant 1 / the first video day
    # -- regardless of how the model ordered its JSON.
    cleaned: list[str] = []
    if isinstance(raw_prompts, list):
        action_prompts: list[str] = []
        other_prompts: list[str] = []
        for item in raw_prompts:
            if isinstance(item, dict):
                text = str(item.get("prompt", "")).strip()
                direction = str(item.get("direction", "")).strip().lower()
            else:
                text, direction = str(item).strip(), ""
            if text:
                (action_prompts if direction == "action" else other_prompts).append(text)
        cleaned = action_prompts + other_prompts

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