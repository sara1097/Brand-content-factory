import json
import random
from datetime import datetime, timezone

from dotenv import load_dotenv

from config import DEFAULT_MODEL
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

Generate exactly 7 posts.

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


def enforce_format_diversity(calendar: dict) -> dict:

    days = calendar["days"]

    formats_used = {
        d["content_format"]
        for d in days
    }

    static_days = [
        d
        for d in days
        if d["content_format"] == "static_post"
    ]

    needed = []

    if not formats_used & VIDEO_FORMATS:
        needed.append(
            random.choice(
                list(VIDEO_FORMATS)
            )
        )

    if not formats_used & VISUAL_FORMATS:
        needed.append(
            random.choice(
                list(VISUAL_FORMATS)
            )
        )

    if "poll" not in formats_used:
        needed.append("poll")

    for fmt, day in zip(
        needed,
        static_days,
    ):

        day["content_format"] = fmt

        if (
            fmt in VISUAL_FORMATS
            and not day.get("visual_notes")
        ):

            day["visual_notes"] = (
                f"Break '{day['post_idea']}' "
                "into 3-5 slides."
            )

    return calendar
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

            calendar = enforce_format_diversity(
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