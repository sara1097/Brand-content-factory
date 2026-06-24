import json
import os
import re
import requests
from pydantic import BaseModel


class VariantInput(BaseModel):
    day: int
    campaign_goal: str
    target_audience: str
    platform: str
    tone: str
    core_message: str
    top_hooks: list[str]
    primary_cta: str


class AdVariant(BaseModel):
    angle: str
    hook: str
    body: str
    cta: str


class ABVariantsOutput(BaseModel):
    variant_a: AdVariant
    variant_b: AdVariant
    variant_c: AdVariant


with open("test_input.json", "r", encoding="utf-8") as f:
    data = VariantInput(**json.load(f))


prompt = f"""
You are an expert marketing copywriter.

Generate exactly 3 ad variants.

Use ONLY the information provided.

Restrictions:

* Do not invent products.
* Do not invent offers.
* Do not invent discounts.
* Do not invent promotions.
* Do not invent statistics.
* Do not invent research findings.
* Do not invent scientific claims.
* Do not invent features.
* Do not invent deadlines.
* Do not invent scarcity.
* Do not invent benefits that are not explicitly implied by the core message.
* Do not claim specific outcomes unless explicitly provided.

If information is missing, keep the content generic.

Variant A:

* Angle: Emotional
* Focus on feelings, aspirations, motivation, and personal impact.

Variant B:

* Angle: Rational
* Focus on logic, usefulness, practical value, and clear benefits.

Variant C:

* Angle: Urgency
* Encourage immediate action.
* Do not use discounts, offers, deadlines, promotions, or scarcity.

Hook Rules:

* Each hook must be unique.
* Never reuse a hook.
* Never copy a hook directly from Top Hooks.
* Use Top Hooks only as inspiration.
* Maximum 10 words.
* Hook cannot be empty.
* Every field must contain meaningful text.

Body Rules:

* Maximum 25 words.
* Keep the message concise.
* Stay aligned with the variant angle.

CTA Rules:

* Maximum 8 words.
* Use the provided Primary CTA as inspiration.
* Keep CTAs short and action-oriented.

Campaign Details:

Day: {data.day}
Campaign Goal: {data.campaign_goal}
Target Audience: {data.target_audience}
Platform: {data.platform}
Tone: {data.tone}
Core Message: {data.core_message}
Top Hooks: {data.top_hooks}
Primary CTA: {data.primary_cta}

Return ONLY valid JSON in this exact format:

{{
"variant_a": {{
"angle": "Emotional",
"hook": "",
"body": "",
"cta": ""
}},
"variant_b": {{
"angle": "Rational",
"hook": "",
"body": "",
"cta": ""
}},
"variant_c": {{
"angle": "Urgency",
"hook": "",
"body": "",
"cta": ""
}}
}}
"""



print("Calling Ollama...")

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen3:4b",
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return only valid JSON. "
                    "No explanations. "
                    "No reasoning. "
                    "No markdown. "
                    "No text outside JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    },
    timeout=300
)

response.raise_for_status()

result = response.json()

if "message" in result:
    raw = result["message"].get("content", "")
elif "response" in result:
    raw = result.get("response", "")
else:
    raw = ""


def parse_variants(raw_text: str) -> ABVariantsOutput:
    raw_text = re.sub(
        r"<think>.*?</think>",
        "",
        raw_text,
        flags=re.DOTALL
    ).strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    json_text = raw_text[start:end + 1]

    parsed = json.loads(json_text)

    return ABVariantsOutput(**parsed)


try:
    variants = parse_variants(raw)

    hooks = [
        variants.variant_a.hook.lower().strip(),
        variants.variant_b.hook.lower().strip(),
        variants.variant_c.hook.lower().strip()
    ]

    if len(set(hooks)) != 3:
        print("\nWarning: Duplicate hooks detected")

    empty_fields = False

    for variant in [
        variants.variant_a,
        variants.variant_b,
        variants.variant_c
    ]:
        if not variant.hook.strip():
            print("Warning: Empty hook detected")
            empty_fields = True

        if not variant.body.strip():
            print("Warning: Empty body detected")
            empty_fields = True

        if not variant.cta.strip():
            print("Warning: Empty CTA detected")
            empty_fields = True

    if empty_fields:
        print("Warning: One or more variants contain empty fields")

    print("\n" + "=" * 50)
    print("VARIANTS GENERATED SUCCESSFULLY")
    print("=" * 50)

    for label, variant in [
        ("A - Emotional", variants.variant_a),
        ("B - Rational", variants.variant_b),
        ("C - Urgency", variants.variant_c)
    ]:
        print(f"\nVariant {label}")
        print(f"Hook: {variant.hook}")
        print(f"Body: {variant.body}")
        print(f"CTA : {variant.cta}")

    os.makedirs("outputs", exist_ok=True)

    with open(
        "outputs/variants_output.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            variants.model_dump(),
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\nSaved to outputs/variants_output.json")

except Exception as e:
    print(f"\nParse Error: {e}")
    print("\nRaw Response:")
    print(raw)