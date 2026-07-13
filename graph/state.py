"""
Shared state for the LangGraph pipeline.

One key per pipeline node output (same keys the Streamlit dashboard
uses), plus the run inputs. Nodes that fail store
{"node_error": ..., "message": ...} under their key instead of raising,
so a failing node never kills the run -- exactly the fault-tolerance
contract the old hand-written runner in app_qwen.py had.
"""
from __future__ import annotations

from typing import TypedDict


class PipelineState(TypedDict, total=False):
    # -------- run inputs --------
    description: str
    uploaded_image_path: str | None
    business_constraints: dict
    # Per-run override of config.ENABLE_VIDEO_GENERATION (sidebar toggle).
    enable_video: bool

    # -------- image acquisition --------
    # Full acquisition result (source, query, rejected candidates, ...).
    image_acquisition: dict
    # The resolved product reference image every downstream consumer
    # (vision analysis, WanGP, Magic Hour) uses. None = run without one.
    image_path: str | None

    # -------- analysis chain --------
    product: dict
    research: dict
    marketing: dict
    content: dict
    variants: dict
    compliance: dict

    # -------- media generation (parallel branch) --------
    video: dict     # 2 WanGP videos for the calendar's video days
    images: dict    # 4 Magic Hour images for the calendar's image days

    # -------- final outputs --------
    final_calendar: dict   # 7-day plan with media paths attached per day
    report: dict
