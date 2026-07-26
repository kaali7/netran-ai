"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: jd_parser.py
Description: Class-based Job Description (JD) parser extracting role, company, tech stack, and queries.
"""

import json
import logging
from typing import Optional

try:
    from .schemas import ParsedJD
    from .gemini_client import GeminiClient
    from .prompts import JD_PARSER_PROMPT_TEMPLATE
except ImportError:
    try:
        from model.research_model.model.schemas import ParsedJD
        from model.research_model.model.gemini_client import GeminiClient
        from model.research_model.model.prompts import JD_PARSER_PROMPT_TEMPLATE
    except ImportError:
        from schemas import ParsedJD
        from gemini_client import GeminiClient
        from prompts import JD_PARSER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class JDParser:
    """Class-based JD parser leveraging Gemini to extract structured role metadata."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client or GeminiClient()

    def parse(self, jd_text: str) -> ParsedJD:
        """
        Parses raw JD text using Gemini to extract structured metadata and 2-3 search queries.

        Args:
            jd_text: Unformatted raw text of the job description.

        Returns:
            ParsedJD Pydantic object containing role, company, tech stack, and search queries.
        """
        prompt = JD_PARSER_PROMPT_TEMPLATE.format(jd_text=jd_text)
        raw_json = self.gemini_client.call(prompt, json_mode=True, temperature=0.2)
        clean_json = self.gemini_client.strip_fences(raw_json)
        return ParsedJD.model_validate_json(clean_json)


# Backward compatibility wrapper
def parse_jd(jd_text: str) -> ParsedJD:
    return JDParser().parse(jd_text)
