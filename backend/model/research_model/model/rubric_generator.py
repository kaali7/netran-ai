"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: rubric_generator.py
Description: Class-based Rubric Generator synthesizing JD text, role metadata, and web market context into InterviewRubric.
"""

import logging

try:
    from .gemini_client import GeminiClient
    from .prompts import RUBRIC_GENERATOR_PROMPT_TEMPLATE
    from .schemas import InterviewRubric, ParsedJD
except ImportError:
    try:
        from model.research_model.model.gemini_client import GeminiClient
        from model.research_model.model.prompts import RUBRIC_GENERATOR_PROMPT_TEMPLATE
        from model.research_model.model.schemas import InterviewRubric, ParsedJD
    except ImportError:
        from gemini_client import GeminiClient
        from prompts import RUBRIC_GENERATOR_PROMPT_TEMPLATE
        from schemas import InterviewRubric, ParsedJD

logger = logging.getLogger(__name__)


class RubricGenerator:
    """Class-based rubric synthesizer leveraging Gemini to generate InterviewRubric."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini_client = gemini_client or GeminiClient()

    def generate(self, jd_text: str, parsed_jd: ParsedJD, search_context: list[dict[str, str]]) -> InterviewRubric:
        """
        Synthesizes raw JD and live market search context into a structured Interview Rubric.
        """
        if search_context:
            context_str = "\n".join([
                f"--- Source ({item.get('url', 'N/A')}): {item.get('title', '')} ---\n{item.get('content', '')}\n"
                for item in search_context
            ])
        else:
            context_str = "No web search context retrieved. Rely on detailed technical baseline knowledge."

        prompt = RUBRIC_GENERATOR_PROMPT_TEMPLATE.format(
            jd_text=jd_text,
            role=parsed_jd.role,
            company=parsed_jd.company,
            tech_stack=', '.join(parsed_jd.tech_stack),
            context_str=context_str
        )

        raw_json = self.gemini_client.call(prompt, json_mode=True, temperature=0.3)
        clean_json = self.gemini_client.strip_fences(raw_json)
        return InterviewRubric.model_validate_json(clean_json)


# Backward compatibility wrapper
def generate_rubric(jd_text: str, parsed_jd: ParsedJD, search_context: list[dict[str, str]]) -> InterviewRubric:
    return RubricGenerator().generate(jd_text, parsed_jd, search_context)
