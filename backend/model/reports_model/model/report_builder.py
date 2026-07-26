"""
Netran AI — Stage 4: Post-Session Multimodal Evaluation & Report Generation Engine
Module: report_builder.py (Backward Compatibility Re-export)
Description: Re-exports Stage4Pipeline, render_markdown_report, and build_report from pipeline.py.
"""

from .pipeline import (
    Stage4Pipeline,
    build_report,
    render_markdown_report,
)

__all__ = [
    "Stage4Pipeline",
    "render_markdown_report",
    "build_report",
]
