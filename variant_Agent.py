import json
import os
import re
import requests
from pydantic import BaseModel


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
    data = json.load(f)

prompt = f"""
Generate 3 short ad variants.

Use ONLY the information provided.
Do not invent products.
Do not invent offers.
Do not invent discounts.
Do not invent features.
Do not mention bottles, drinks, apps, products, statistics, research, or claims unless explicitly provided.

Base every variant only on the campaign message and audience.

Variant A must be emotional.
Variant B must be rational.
Variant C must create urgency.

Each variant must be clearly different from the others.

Each hook must be under 10 words.
Each body must be under 25 words.
Each CTA must be under 8 words.

Campaign:
Message: {data["core_message"]}
Audience: {data["target_audience"]}

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
        "model": "qwen2.5:3b",
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

print("\n=== FULL RESPONSE ===")
print(json.dumps(result, indent=2))

if "message" in result:
    raw = result["message"].get("content", "")
elif "response" in result:
    raw = result.get("response", "")
else:
    raw = ""

print("\n=== RAW OUTPUT ===")
print(repr(raw))

print("\n=== RAW OUTPUT ===")
print(raw)


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