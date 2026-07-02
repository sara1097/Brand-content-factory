"""
Main AI Marketing Pipeline
"""

from pathlib import Path
import json

from agents.product_agent import analyze_product
from agents.research_agent import research_market
from agents.marketing_strategy_agent import build_marketing_strategy
from agents.variant_agent import generate_variants
from agents.compliance_agent import generate_compliance
from agents.report_agent import generate_report
from agents.content_agent import generate_content
from agents.video_agent import generate_video_assets

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_json(filename: str, data: dict):
    path = OUTPUT_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {filename}")


def _failed(step: str, result: dict) -> dict:
    return {
        "error": result.get("error", f"{step} failed"),
        "failed_step": step,
    }


def run_pipeline(
    text_description: str,
    image_path: str | None = None,
    business_constraints: dict | None = None,
):
    print("=" * 60)
    print("STEP 1 : PRODUCT")
    print("=" * 60)

    product = analyze_product(text_description, image_path)
    save_json("product.json", product)
    if "error" in product:
        return _failed("product", product)

    print("=" * 60)
    print("STEP 2 : MARKET RESEARCH")
    print("=" * 60)

    research = research_market(product)
    save_json("research.json", research)
    if "error" in research:
        return _failed("research", research)

    print("=" * 60)
    print("STEP 3 : MARKETING STRATEGY")
    print("=" * 60)

    marketing = build_marketing_strategy(product, research, business_constraints)
    save_json("marketing.json", marketing)
    if "error" in marketing:
        return _failed("marketing", marketing)

    print("=" * 60)
    print("STEP 4 : CONTENT CALENDAR")
    print("=" * 60)

    content = generate_content(marketing)
    save_json("content.json", content)

    print("=" * 60)
    print("STEP 5 : VARIANT GENERATION")
    print("=" * 60)

    variants = generate_variants(marketing, content)
    save_json("variants.json", variants)
    if "error" in variants:
        return _failed("variants", variants)

    print("=" * 60)
    print("STEP 6 : COMPLIANCE REVIEW")
    print("=" * 60)

    compliance = generate_compliance(marketing, variants)
    save_json("compliance.json", compliance)
    if "error" in compliance:
        return _failed("compliance", compliance)

    print("=" * 60)
    print("STEP 7 : VIDEO GENERATION")
    print("=" * 60)

    video = generate_video_assets(
        description=text_description,
        product=product,
        marketing=marketing,
        content=content,
        image_path=image_path,
    )
    save_json("video.json", video)

    report = generate_report(
        product,
        research,
        marketing,
        variants,
        compliance,
        content,
    )
    save_json("report.json", report)

    return {
        "product": product,
        "research": research,
        "marketing": marketing,
        "variants": variants,
        "compliance": compliance,
        "content": content,
        "video": video,
        "report": report,
    }


if __name__ == "__main__":

    description = """
    Premium eco-friendly hoodie made from organic cotton.
    Comfortable, durable, and designed for young adults
    interested in sustainable fashion.
    """

    results = run_pipeline(description)

    if "error" in results:
        print(f"\nPipeline failed at step: {results.get('failed_step')}")
        print(results["error"])
    else:
        print("\nPipeline completed successfully.")