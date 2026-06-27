"""
Enterprise AI Business Intelligence System

Entry Point
"""

from core.pipeline import run_pipeline
print("MAIN FILE STARTED")

from reports.report_formatter import format_report

from reports.pdf_generator import generate_pdf


def main():

    print("=" * 60)
    print("Enterprise AI Business Intelligence System")
    print("=" * 60)

    text_description = input(
        "\nEnter product description:\n> "
    )

    image_path = input(
        "\nImage path (optional):\n> "
    ).strip()

    if image_path == "":
        image_path = None

    business_constraints = {

        "country": "Egypt",

        "budget": "Medium",

        "campaign_duration": "6 Months",

        "primary_goal": "Increase Sales",

        "brand_stage": "New Product Launch"

    }

    print("\nRunning AI Pipeline...\n")

    results = run_pipeline(

        text_description=text_description,

        image_path=image_path,

        business_constraints=business_constraints

    )

    if "error" in results:

        print("\nPipeline Failed\n")

        print(results)

        return

    print("Formatting Report...")

    formatted_report = format_report(

        results["report"]

    )

    output_file = "Executive_Report.pdf"

    generate_pdf(

        formatted_report,

        output_file

    )

    print("\nDone!")

    print(f"\nPDF Saved As: {output_file}")


if __name__ == "__main__":

    main()