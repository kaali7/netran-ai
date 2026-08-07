"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: prompt_builder.py
Description: Class-based Stage2PromptBuilder extracting Stage 1 market context and constructing base instructions for Stage 2 synthesis.
"""

import json
from typing import Any

try:
    from .prompts import SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE
except ImportError:
    try:
        from model.question_model.model.prompts import (
            SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE,
        )
    except ImportError:
        from prompts import SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE


class Stage2PromptBuilder:
    """Class-based prompt builder formatting baseline instructions and context for Stage 2."""

    @staticmethod
    def extract_job_context(job_input: dict[str, Any]) -> dict[str, Any]:
        """
        Extracts job metadata from both Stage 1 nested output JSON and legacy flat JD JSON.
        Returns a standardized dictionary with company, role, target_seniority, and rubric_json string.
        """
        if "parsed_jd" in job_input and isinstance(job_input["parsed_jd"], dict):
            parsed_jd = job_input.get("parsed_jd", {})
            return {
                "company": parsed_jd.get("company", job_input.get("company", "Target Company")),
                "role": parsed_jd.get("role", job_input.get("role", "Target Role")),
                "target_seniority": parsed_jd.get("target_seniority", job_input.get("target_seniority", "Senior")),
                "rubric_json": json.dumps(job_input, indent=2)
            }
        else:
            # Standalone or flat JD JSON fallback
            return {
                "company": job_input.get("company", "Target Company"),
                "role": job_input.get("role", "Target Role"),
                "target_seniority": job_input.get("target_seniority", "Senior"),
                "rubric_json": json.dumps(job_input, indent=2)
            }

    def build_instructions(self, target_seniority: str) -> str:
        """
        Returns base instruction guardrails for Gemini to construct Stage 3's behavioral system prompt.
        """
        return SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE.format(target_seniority=target_seniority)


# Backward compatibility wrapper
class PromptBuilder(Stage2PromptBuilder):
    pass


def get_system_prompt_instructions(target_seniority: str) -> str:
    return Stage2PromptBuilder().build_instructions(target_seniority)
