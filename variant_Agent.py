import json
import os
import re
import time
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ─── Data Models ─────────────────────────────────────────────────────────────

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


# ─── Load Input ───────────────────────────────────────────────────────────────

with open("test_input.json", "r", encoding="utf-8") as f:
    data = VariantInput(**json.load(f))


# ─── Prompt Builder ───────────────────────────────────────────────────────────

def build_prompt(data: VariantInput) -> str:
    hooks_text = "\n".join(f"- {h}" for h in data.top_hooks)

    return f"""You are a senior social media copywriter for {data.platform}.

Generate 3 COMPLETELY DIFFERENT ad variants for A/B testing.
Each variant must use a distinct persuasion strategy, as if written by a different copywriter.

CAMPAIGN DETAILS:
- Product Message: {data.core_message}
- Audience: {data.target_audience}
- Platform: {data.platform}
- Tone: {data.tone}
- Goal: {data.campaign_goal}
- Primary CTA Reference: {data.primary_cta}

INSPIRATION HOOKS (use as creative inspiration only — do NOT copy):
{hooks_text}

VARIANT INSTRUCTIONS:

VARIANT A — EMOTIONAL
- Appeal to feelings, aspirations, personal connection, or belonging.
- Open with a relatable situation or human moment.
- Reinforce the product message through emotional resonance.
- CTA must feel supportive and encouraging.

VARIANT B — RATIONAL
- Lead with a clear problem the audience faces daily.
- Focus on usefulness, logic, and tangible relevance.
- CTA must be practical and action-oriented.
- Explain practically how the product relates to the audience's needs using only the provided campaign information.

VARIANT C — URGENCY
- Frame the message around immediate relevance (not fake deadlines or scarcity).
- Highlight why taking action now is relevant based only on the campaign details.
- Motivate a confident next step.
- CTA must be direct and momentum-driven.

STRICT RULES:
- All 3 hooks must be completely different from each other.
- All 3 CTAs must be unique and angle-specific.
- Do NOT use: Learn More / Act Now / Start Today / Do It Now / Discover More / Click Here
- Do NOT invent discounts, statistics, promotions, or claims not in the campaign details.
- Do NOT repeat the hook inside the body.
- Body must be 2–4 sentences. Hook must be 1 punchy sentence.
- Write copy that feels real, human, and platform-native for {data.platform}.
- Do NOT rephrase the same idea twice within the same body. 
- Each sentence must add NEW information or a NEW angle.

Return ONLY this valid JSON — no markdown, no explanation, no text outside JSON:

{{
  "variant_a": {{"angle": "Emotional", "hook": "", "body": "", "cta": ""}},
  "variant_b": {{"angle": "Rational",  "hook": "", "body": "", "cta": ""}},
  "variant_c": {{"angle": "Urgency",   "hook": "", "body": "", "cta": ""}}
}}"""


# ─── Parser ───────────────────────────────────────────────────────────────────

def parse_variants(raw_text: str) -> ABVariantsOutput:
    # Strip thinking tags (some models emit these)
    raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
    # Strip markdown code fences if present
    raw_text = re.sub(r"```(?:json)?", "", raw_text)
    raw_text = raw_text.strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in response")

    json_text = raw_text[start:end + 1]
    parsed = json.loads(json_text)
    return ABVariantsOutput(**parsed)


# ─── API Call with Retry ──────────────────────────────────────────────────────

def call_groq_with_retry(prompt: str, max_attempts: int = 3) -> ABVariantsOutput:
    last_error = None

    for attempt in range(1, max_attempts + 1):
        print(f"Calling Groq... (attempt {attempt}/{max_attempts})")
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert marketing copywriter for social media advertising. "
                            "Generate persuasive, audience-specific ad copy for the requested angles. "
                            "Return ONLY valid JSON. No markdown. No explanations. No text outside JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1500
            )

            raw = response.choices[0].message.content
            return parse_variants(raw)

        except Exception as e:
            last_error = e
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_attempts:
                time.sleep(2)

    raise RuntimeError(f"All {max_attempts} attempts failed. Last error: {last_error}")


# ─── Quality Checks ───────────────────────────────────────────────────────────

BANNED_CTAS = {"learn more", "act now", "start today", "do it now", "discover more", "click here"}

def run_quality_checks(variants: ABVariantsOutput) -> bool:
    all_ok = True
    items = [
        ("A - Emotional", variants.variant_a),
        ("B - Rational",  variants.variant_b),
        ("C - Urgency",   variants.variant_c),
    ]

    for label, v in items:
        if not v.hook.strip():
            print(f"[WARN] Variant {label}: empty hook")
            all_ok = False
        elif len(v.hook.split()) < 2:
            print(f"[WARN] Variant {label}: hook too short ({v.hook!r})")

        if not v.body.strip():
            print(f"[WARN] Variant {label}: empty body")
            all_ok = False
        elif len(v.body.split()) < 8:
            print(f"[WARN] Variant {label}: body too short")

        if not v.cta.strip():
            print(f"[WARN] Variant {label}: empty CTA")
            all_ok = False
        elif v.cta.lower().strip() in BANNED_CTAS:
            print(f"[WARN] Variant {label}: banned generic CTA used ({v.cta!r})")

        if v.hook.lower() in v.body.lower():
            print(f"[WARN] Variant {label}: hook repeated inside body")

    hooks = [v.hook.lower().strip() for _, v in items]
    if len(set(hooks)) != 3:
        print("[WARN] Duplicate hooks detected across variants")
        all_ok = False

    ctas = [v.cta.lower().strip() for _, v in items]
    if len(set(ctas)) != 3:
        print("[WARN] Duplicate CTAs detected across variants")
        all_ok = False

    return all_ok


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    prompt = build_prompt(data)
    variants = call_groq_with_retry(prompt)

    print()
    quality_ok = run_quality_checks(variants)

    print("\n" + "=" * 50)
    print("VARIANTS GENERATED SUCCESSFULLY" if quality_ok else "VARIANTS GENERATED (WITH WARNINGS)")
    print("=" * 50)

    for label, variant in [
        ("A - Emotional", variants.variant_a),
        ("B - Rational",  variants.variant_b),
        ("C - Urgency",   variants.variant_c),
    ]:
        print(f"\nVariant {label}")
        print(f"Hook : {variant.hook}")
        print(f"Body : {variant.body}")
        print(f"CTA  : {variant.cta}")

    os.makedirs("outputs", exist_ok=True)
    output_path = "outputs/variants_output.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(variants.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()