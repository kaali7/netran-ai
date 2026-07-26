"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: question_generator.py (Backward Compatibility Re-export)
Description: Re-exports Stage2Pipeline and helper functions from pipeline.py.
"""

from .pipeline import (
    Stage2Pipeline,
    generate_fallback_stage2_output,
    generate_stage2_output,
)

__all__ = [
    "Stage2Pipeline",
    "generate_stage2_output",
    "generate_fallback_stage2_output",
]
