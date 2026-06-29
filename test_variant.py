import json

from agents.variant_agent import generate_variants

print("Loading marketing.json...")

with open(
    "outputs/20260626_200438/marketing.json",
    "r",
    encoding="utf-8"
) as f:
    marketing = json.load(f)

print("Generating variants...")

result = generate_variants(marketing)

print("\n========== RESULT ==========\n")

print(json.dumps(result, indent=2, ensure_ascii=False))