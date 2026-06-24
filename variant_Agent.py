import json
import os
import re
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

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
You are an expert social media copywriter for {data.platform}.

Your task is to generate 3 COMPLETELY DIFFERENT ad variants for A/B testing.

Each variant must feel like it was written by a different copywriter using a different persuasion strategy.

CAMPAIGN DETAILS:

* Product Message: {data.core_message}
* Audience: {data.target_audience}
* Platform: {data.platform}
* Tone: {data.tone}
* Goal: {data.campaign_goal}
* Primary CTA: {data.primary_cta}

INSPIRATION HOOKS (use as inspiration, do NOT copy directly):

{chr(10).join(f'- {h}' for h in data.top_hooks)}

VARIANT A — EMOTIONAL

* Focus on emotions, feelings, aspirations, belonging, motivation, or personal connection.
* Describe a relatable situation or feeling.
* Reinforce the campaign message in a motivating way.
* CTA should be supportive and encouraging.

VARIANT B — RATIONAL

* Focus on logic, practicality, usefulness, and daily relevance.
* Clearly describe the problem.
* Explain why the campaign message matters in everyday life.
* CTA should be practical and action-oriented.

VARIANT C — URGENCY

* Encourage immediate action.
* Explain why the message matters right now.
* Encourage a simple next step.
* Do not use fake urgency.
* Do not use scarcity.
* Do not use deadlines.
* Do not use countdowns.
* Do not use pressure tactics.
* CTA should be direct and action-oriented.

CTA RULES

* Every CTA must be unique.
* Every CTA must match its variant angle.
* Every CTA must be relevant to the campaign.
* Generic CTAs are not allowed.

Do NOT use:

* Learn More
* Act Now
* Start Today
* Do It Now
* Discover More
* Click Here

GLOBAL RULES

* Hooks must be concise, engaging, and audience-relevant.
* Bodies must sound like real marketing copy.
* Hooks must be different across all variants.
* CTAs must be different across all variants.
* Use only information provided in the campaign details.
* Do not invent products.
* Do not invent discounts.
* Do not invent promotions.
* Do not invent offers.
* Do not invent statistics.
* Do not invent research findings.
* Do not invent scientific claims.
* Do not introduce benefits, outcomes, or claims that are not explicitly present in the campaign details.
* Do not use filler text.
* Do not repeat the hook inside the body.

GLOBAL RULES

* Hooks must be concise, engaging, and audience-relevant.
* Bodies must sound like real marketing copy.
* Hooks must be different across all variants.
* CTAs must be different across all variants.
* Use only information provided in the campaign details.
* Do not invent products.
* Do not invent discounts.
* Do not invent promotions.
* Do not invent offers.
* Do not invent statistics.
* Do not invent research findings.
* Do not invent scientific claims.
* Do not introduce benefits, outcomes, or claims that are not explicitly present in the campaign details.
* Do not use filler text.
* Do not repeat the hook inside the body.

LENGTH GUIDELINES

* Adapt the response length to the amount of information provided.
* Short campaign inputs should produce concise outputs.
* Detailed campaign inputs may produce richer outputs.
* The amount of generated content should be proportional to the amount of campaign information provided.
* Do not add unnecessary details.
* Do not remove important context.
* Keep the copy suitable for social media advertising.
* Avoid extremely short responses.
* Avoid unnecessarily long paragraphs.

Return ONLY valid JSON using EXACTLY this structure:

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



print("Calling Groq...")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an expert marketing copywriter specialized in social media advertising. "
                "Generate persuasive, audience-specific ad copy. "
                "Follow the requested angle precisely. "
                "Return only valid JSON. "
                "No explanations. "
                "No markdown. "
                "No text outside JSON."
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.7,
    max_tokens=800
)

raw = response.choices[0].message.content


def parse_variants(raw_text: str) -> ABVariantsOutput:
    raw_text = re.sub(
        r"<think>.*?</think>",
        "",
        raw_text,
        flags=re.DOTALL
    )

    raw_text = raw_text.strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    json_text = raw_text[start:end + 1]

    parsed = json.loads(json_text)

    return ABVariantsOutput(**parsed)


try:
    variants = parse_variants(raw)
    for variant in [
        variants.variant_a,
        variants.variant_b,
        variants.variant_c
    ]:
        if len(variant.body.split()) < 8:
            print("Warning: Body too short")

        if len(variant.hook.split()) < 2:
            print("Warning: Hook too short")
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