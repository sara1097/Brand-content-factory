import json
from datetime import datetime, timezone

from dotenv import load_dotenv

from config import DEFAULT_MODEL, MEDIA_MIX
from tools.groq_client import create_chat_completion

load_dotenv()

GROQ_MODEL = DEFAULT_MODEL

CONTENT_FORMATS = [
    "static_post",
    "carousel",
    "infographic",
    "poll",
    "reel",
    "tiktok",
    "youtube_short",
]

VIDEO_FORMATS = {
    "reel",
    "tiktok",
    "youtube_short",
}

VISUAL_FORMATS = {
    "carousel",
    "infographic",
}

MEDIA_TYPES = ("video", "image", "text")

SYSTEM_PROMPT = f"""
You are a social media content strategist.

Return ONLY valid JSON.

{{
    "campaign_name":"string",
    "days":[
        {{
            "day":1,
            "journey_stage":"string",
            "platform":"string",
            "media_type":"one of ["video", "image", "text"]",
            "content_format":"one of {CONTENT_FORMATS}",
            "content_pillar":"string",
            "post_idea":"string",
            "hook":"string",
            "caption":"string",
            "hashtags":["#tag"],
            "cta":"string",
            "visual_notes":"string"
        }}
    ]
}}

Generate exactly 7 posts (day 1 to day 7).

MEDIA MIX (mandatory): exactly {MEDIA_MIX["video"]} days with
media_type "video" (an AI-generated product video will be rendered for
them), exactly {MEDIA_MIX["image"]} days with media_type "image" (an
AI-generated product image will be rendered for them), and exactly
{MEDIA_MIX["text"]} day with media_type "text" (caption only, no media).

- "video" days must use a video content_format (reel/tiktok/youtube_short).
- "image" days must use a visual content_format (static_post/carousel/infographic).
- The "text" day should be a poll or text-only discussion post.
- For video and image days, make visual_notes a concrete art direction
  for the generated media (setting, lighting, mood, focus).

Return JSON only.
"""
def build_user_prompt(strategy: dict, campaign_name: str) -> str:

    personas = strategy["customer_personas"]

    if isinstance(personas, dict):
        personas = [personas]

    personas_text = "\n".join(
        f"- {p.get('name','Persona')}: "
        f"audience={p.get('target_audience')}, "
        f"pain_points={p.get('pain_points')}, "
        f"motivations={p.get('motivations')}"
        for p in personas
    )

    journey = strategy.get("customer_journey", {})

    if isinstance(journey, dict):
        journey_text = "\n".join(
            f"- {k}: {v}"
            for k, v in journey.items()
        )
        stage_names = list(journey.keys())
    else:
        journey_text = "\n".join(
            f"- {x}" for x in journey
        )
        stage_names = journey

    return f"""
Campaign Name:
{campaign_name}

PERSONAS
{personas_text}

Marketing Angles:
{strategy.get("marketing_angles", [])}

Campaign Ideas:
{strategy.get("campaign_ideas", [])}

SWOT:
{strategy.get("swot", {})}

Customer Journey:
{journey_text}

Use ONLY these stages:
{stage_names}

Return ONLY JSON.
"""
def extract_json(raw_text: str) -> dict:
    text = raw_text.strip().strip("`")

    start = text.find("{")
    end = text.rfind("}")

    return json.loads(
        text[start:end + 1]
    )


def clean_calendar(calendar: dict) -> dict:

    for day in calendar.get("days", []):

        day["hashtags"] = [
            h if h.startswith("#")
            else f"#{h}"
            for h in day.get("hashtags", [])
        ]

    return calendar


def enforce_media_mix(calendar: dict, media_mix: dict | None = None) -> dict:
    """
    Deterministically guarantee the weekly media plan (default: 2 video
    days + 4 image days + 1 text-only day) no matter what the LLM
    returned, and keep content_format consistent with each media_type.
    Downstream, video days drive WanGP and image days drive Magic Hour.
    """

    quotas = dict(media_mix or MEDIA_MIX)

    days = calendar.get("days", [])[: sum(quotas.values())]

    # Pad if the LLM returned fewer than 7 days, so the mix stays exact.
    while len(days) < sum(quotas.values()):
        days.append({
            "day": len(days) + 1,
            "platform": "instagram",
            "content_format": "static_post",
            "post_idea": f"{calendar.get('campaign_name', 'Campaign')} highlight",
            "hook": "",
            "caption": "",
            "hashtags": [],
            "cta": "",
            "visual_notes": "",
        })

    calendar["days"] = days

    # Pass 1: keep declared media_type while its quota lasts.
    remaining = dict(quotas)

    for day in days:
        declared = day.get("media_type")
        if declared in MEDIA_TYPES and remaining[declared] > 0:
            remaining[declared] -= 1
        else:
            day["media_type"] = None

    # Pass 2: infer from content_format where possible, then fill with
    # whatever quota is left, in day order.
    for day in days:
        if day["media_type"]:
            continue

        fmt = day.get("content_format")

        if fmt in VIDEO_FORMATS and remaining["video"] > 0:
            chosen = "video"
        elif fmt in VISUAL_FORMATS | {"static_post"} and remaining["image"] > 0:
            chosen = "image"
        else:
            chosen = next(t for t in MEDIA_TYPES if remaining[t] > 0)

        day["media_type"] = chosen
        remaining[chosen] -= 1

    # Pass 3: content_format must match the media_type.
    for i, day in enumerate(days):
        day["day"] = i + 1
        fmt = day.get("content_format")

        if day["media_type"] == "video" and fmt not in VIDEO_FORMATS:
            day["content_format"] = "reel"
        elif day["media_type"] == "image" and fmt not in VISUAL_FORMATS | {"static_post"}:
            day["content_format"] = "static_post"
        elif day["media_type"] == "text" and fmt not in {"poll", "static_post"}:
            day["content_format"] = "poll"

        if day["media_type"] in {"video", "image"} and not day.get("visual_notes"):
            day["visual_notes"] = (
                f"Product-centered visual for: {day.get('post_idea', 'the campaign')}."
            )

    return calendar


def days_by_media_type(calendar: dict, media_type: str) -> list[dict]:
    """Calendar days of one media_type ("video" / "image" / "text")."""
    return [
        day
        for day in calendar.get("days", [])
        if day.get("media_type") == media_type
    ]
def generate_content_calendar(
    strategy: dict,
    campaign_name: str,
    max_attempts: int = 2,
    model: str | None = None,
    max_completion_tokens: int = 4096,
) -> dict:

    resolved_model = model or GROQ_MODEL

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },

        {
            "role": "user",
            "content": build_user_prompt(
                strategy,
                campaign_name,
            ),
        },

    ]

    last_error = None

    for attempt in range(max_attempts):

        try:

            response = create_chat_completion(

                model=resolved_model,

                messages=messages,

                temperature=0.7,

                max_completion_tokens=max_completion_tokens,

                response_format={
                    "type": "json_object"
                },

            )

            calendar = extract_json(
                response.choices[0].message.content
            )

            calendar = clean_calendar(calendar)

            calendar = enforce_media_mix(
                calendar
            )

            calendar["campaign_name"] = campaign_name

            calendar["generated_at"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            calendar["model_used"] = (
                f"groq/{resolved_model}"
            )

            return calendar

        except Exception as e:

            last_error = e

            print(
                f"[WARN] Attempt {attempt + 1} failed: {e}"
            )

    raise last_error