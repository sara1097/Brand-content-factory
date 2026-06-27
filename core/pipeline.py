"""
Enterprise AI Pipeline

Runs the complete Business Intelligence workflow.
"""

import time
from datetime import datetime, timezone

from agents.product_agent import analyze_product

from agents.research_agent import research_market

from agents.marketing_strategy_agent import (
    build_marketing_strategy,
)

from agents.report_agent import (
    generate_report,
)

def run_pipeline(

    text_description: str,

    image_path: str | None = None,

    business_constraints: dict | None = None,

) -> dict:

    """
    Run the complete AI pipeline.
    """

    start_time = time.time()

    product = analyze_product(

        text_description,

        image_path

    )

    if "error" in product:

        return product

    research = research_market(

        product

    )

    if "error" in research:

        return research

    marketing = build_marketing_strategy(

        product,

        research,

        business_constraints

    )

    if "error" in marketing:

        return marketing

    report = generate_report(

        product,

        research,

        marketing

    )

    if "error" in report:

        return report

    end_time = time.time()
    
    execution_time = round(end_time - start_time, 2)
    
    generated_at = datetime.now(timezone.utc).isoformat()

    return {

        "status": "success",

        "pipeline_version": "1.0.0",

        "generated_at": generated_at,

        "execution_time": execution_time,

        "product": product,

        "research": research,

        "marketing": marketing,

        "report": report

    }