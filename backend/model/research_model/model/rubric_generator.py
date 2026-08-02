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


import json


class RubricGenerator:
    """Class-based rubric synthesizer leveraging Gemini to generate InterviewRubric."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini_client = gemini_client or GeminiClient()

    def generate(self, jd_text: str, parsed_jd: ParsedJD, search_context: list[dict[str, str]]) -> InterviewRubric:
        """
        Synthesizes raw JD and live market search context into a structured Interview Rubric.
        """
        if search_context:
            context_blocks = []
            for item in search_context:
                vector_label = item.get("vector", "Search Intelligence")
                title = item.get("title", "Market Intel Source")
                url = item.get("url", "N/A")
                content = item.get("content", "")
                context_blocks.append(f"=== VECTOR: {vector_label} ({title} - {url}) ===\n{content}\n")
            context_str = "\n".join(context_blocks)
        else:
            context_str = "No web search context retrieved. Rely on detailed technical baseline knowledge."

        prompt = RUBRIC_GENERATOR_PROMPT_TEMPLATE.format(
            jd_text=jd_text,
            role=parsed_jd.role,
            company=parsed_jd.company,
            target_seniority=getattr(parsed_jd, "target_seniority", "Senior"),
            tech_stack=", ".join(parsed_jd.tech_stack),
            context_str=context_str
        )

        raw_json = self.gemini_client.call(prompt, json_mode=True, temperature=0.3)
        clean_json = self.gemini_client.strip_fences(raw_json)

        try:
            return InterviewRubric.model_validate_json(clean_json)
        except Exception as err:
            logger.warning(f"Strict InterviewRubric validation failed ({err}). Attempting fallback dict parsing.")
            try:
                data = json.loads(clean_json)
                if isinstance(data, dict):
                    return InterviewRubric.model_validate(data)
                raise ValueError("Parsed output is not a JSON dictionary")
            except Exception as parse_err:
                logger.error(f"Failed fallback parsing for InterviewRubric: {parse_err}")
                # Construct minimal valid rubric object on failure
                return InterviewRubric(
                    roleOverview=f"Target role overview for {parsed_jd.role} at {parsed_jd.company}",
                    keyTechnicalPillars=parsed_jd.tech_stack[:3] or ["System Design", "Core Engineering"],
                    expectedInterviewTopics=[]
                )


# Backward compatibility wrapper
def generate_rubric(jd_text: str, parsed_jd: ParsedJD, search_context: list[dict[str, str]]) -> InterviewRubric:
    return RubricGenerator().generate(jd_text, parsed_jd, search_context)

