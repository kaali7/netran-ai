"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: jd_parser.py
Description: Class-based Job Description (JD) parser extracting role, company, tech stack, and queries.
"""

import logging

try:
    from .gemini_client import GeminiClient
    from .prompts import JD_PARSER_PROMPT_TEMPLATE
    from .schemas import ParsedJD
except ImportError:
    try:
        from model.research_model.model.gemini_client import GeminiClient
        from model.research_model.model.prompts import JD_PARSER_PROMPT_TEMPLATE
        from model.research_model.model.schemas import ParsedJD
    except ImportError:
        from gemini_client import GeminiClient
        from prompts import JD_PARSER_PROMPT_TEMPLATE
        from schemas import ParsedJD

logger = logging.getLogger(__name__)


import json


class JDParser:
    """Class-based JD parser leveraging Gemini to extract structured role metadata."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini_client = gemini_client or GeminiClient()

    def parse(self, jd_text: str) -> ParsedJD:
        """
        Parses raw JD text using Gemini to extract structured metadata and 3 search queries.

        Args:
            jd_text: Unformatted raw text of the job description.

        Returns:
            ParsedJD Pydantic object containing role, company, target_seniority, tech_stack, and search_queries.
        """
        prompt = JD_PARSER_PROMPT_TEMPLATE.format(jd_text=jd_text)
        raw_json = self.gemini_client.call(prompt, json_mode=True, temperature=0.2)
        clean_json = self.gemini_client.strip_fences(raw_json)

        try:
            return ParsedJD.model_validate_json(clean_json)
        except Exception as err:
            logger.warning(f"Strict Pydantic parse failed for ParsedJD ({err}). Attempting dictionary repair.")
            try:
                data = json.loads(clean_json)
                if not isinstance(data, dict):
                    raise ValueError("Parsed JSON is not a dict")
                return ParsedJD(
                    role=str(data.get("role", "Target Role")),
                    company=str(data.get("company", "Target Company")),
                    target_seniority=str(data.get("target_seniority", "Senior")),
                    tech_stack=list(data.get("tech_stack", [])),
                    search_queries=list(data.get("search_queries", [
                        f"{data.get('role', 'Developer')} interview questions system design",
                        f"{data.get('role', 'Developer')} salary benchmark compensation 2026",
                        f"{data.get('role', 'Developer')} recruiter screening green flags red flags"
                    ]))
                )
            except Exception as repair_err:
                logger.error(f"Failed to repair ParsedJD JSON: {repair_err}")
                return ParsedJD(
                    role="Software Engineer",
                    company="Target Company",
                    target_seniority="Senior",
                    tech_stack=["General Development"],
                    search_queries=[
                        "Software Engineer interview questions",
                        "Software Engineer salary benchmark USD INR",
                        "Software Engineer recruiter screening flags"
                    ]
                )


# Backward compatibility wrapper
def parse_jd(jd_text: str) -> ParsedJD:
    return JDParser().parse(jd_text)

