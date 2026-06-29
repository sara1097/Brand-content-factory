import json

from agents.variant_agent import generate_variants
from agents.compliance_agent import generate_compliance


print("Loading marketing.json...")

with open(
    "outputs/20260626_200438/marketing.json",
    "r",
    encoding="utf-8"
) as f:
    marketing = json.load(f)


print("Generating variants...")

variants = generate_variants(marketing)


print("Running compliance review...")

result = generate_compliance(
    marketing,
    variants,
)

print("\n========== COMPLIANCE RESULT ==========\n")

print(json.dumps(result, indent=2, ensure_ascii=False))