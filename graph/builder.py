"""
LangGraph pipeline wiring.

    START -> acquire_image -> product -> research -> marketing -> content
                                                                     |
                    +---------------------+--------------------------+
                    v                     v                          v
                variants               video (WanGP)         images (Magic Hour)
                    |                     +------------+-------------+
                    v                                  v
                compliance                     assemble (7-day plan)
                    +---------------------+------------+
                                          v
                                        report -> END

The text-LLM chain stays sequential (Groq's ~6000 TPM budget makes
parallel text calls counterproductive), while the two media branches
run concurrently -- they talk to separate services (Modal / Magic Hour)
and spend most of their time waiting on renders.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from graph import nodes
from graph.state import PipelineState


def build_pipeline_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("acquire_image", nodes.acquire_image_node)
    graph.add_node("product", nodes.product_node)
    graph.add_node("research", nodes.research_node)
    graph.add_node("marketing", nodes.marketing_node)
    graph.add_node("content", nodes.content_node)
    graph.add_node("variants", nodes.variants_node)
    graph.add_node("compliance", nodes.compliance_node)
    graph.add_node("video", nodes.video_node)
    graph.add_node("images", nodes.images_node)
    graph.add_node("assemble", nodes.assemble_calendar_node)
    graph.add_node("report", nodes.report_node)

    # Sequential analysis chain.
    graph.add_edge(START, "acquire_image")
    graph.add_edge("acquire_image", "product")
    graph.add_edge("product", "research")
    graph.add_edge("research", "marketing")
    graph.add_edge("marketing", "content")

    # Fan-out after the calendar.
    graph.add_edge("content", "variants")
    graph.add_edge("content", "video")
    graph.add_edge("content", "images")

    graph.add_edge("variants", "compliance")

    # Joins: assembly needs both media nodes AND the compliance branch
    # (each day's compliance-safe ad variant becomes the plan's
    # "extra_caption"); the report follows the assembled calendar.
    graph.add_edge(["video", "images", "compliance"], "assemble")
    graph.add_edge("assemble", "report")

    graph.add_edge("report", END)

    return graph.compile()


@lru_cache(maxsize=1)
def get_pipeline_graph():
    """Compiled graph, built once per process (Streamlit reruns reuse it)."""
    return build_pipeline_graph()
