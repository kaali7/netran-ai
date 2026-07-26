"""
Netran AI — Stage 2: Contextual Question & Behavioral Prompt Engine
Module: prompt_builder.py
Description: Class-based PromptBuilder constructing base instruction guardrails for Eva persona system prompt.
"""

try:
    from .prompts import SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE
except ImportError:
    try:
        from model.question_model.model.prompts import SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE
    except ImportError:
        from prompts import SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE


class PromptBuilder:
    """Class-based prompt builder formatting baseline instructions for Stage 2."""

    def build_instructions(self, target_seniority: str) -> str:
        """
        Returns base instruction guardrails for Gemini to construct Stage 3's behavioral system prompt.
        """
        return SYSTEM_PROMPT_INSTRUCTIONS_TEMPLATE.format(target_seniority=target_seniority)


# Backward compatibility wrapper
def get_system_prompt_instructions(target_seniority: str) -> str:
    return PromptBuilder().build_instructions(target_seniority)
