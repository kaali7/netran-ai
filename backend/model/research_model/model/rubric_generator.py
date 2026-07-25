"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: rubric_generator.py
Description: Synthesizes raw JD text, extracted role metadata, and live market web context into
             a structured InterviewRubric Pydantic object via Gemini 3.6 Flash.
"""

import json
import logging
from typing import List, Dict
try:
    from .schemas import ParsedJD, InterviewRubric
    from .gemini_client import call_gemini_api
except ImportError:
    try:
        from model.research_model.model.schemas import ParsedJD, InterviewRubric
        from model.research_model.model.gemini_client import call_gemini_api
    except ImportError:
        from schemas import ParsedJD, InterviewRubric
        from gemini_client import call_gemini_api

logger = logging.getLogger(__name__)

def generate_rubric(jd_text: str, parsed_jd: ParsedJD, search_context: List[Dict[str, str]]) -> InterviewRubric:
    """
    Synthesizes raw JD and live market search context into a structured Interview Rubric using Gemini REST API.
    """
    context_str = ""
    if search_context:
        context_str = "\n".join([
            f"--- Source ({item.get('url', 'N/A')}): {item.get('title', '')} ---\n{item.get('content', '')}\n"
            for item in search_context
        ])
    else:
        context_str = "No web search context retrieved. Rely on detailed technical baseline knowledge."

    prompt = f"""
You are an elite Tech Lead and Hiring Bar Raiser creating an interview assessment rubric.

Job Description:
\"\"\"
{jd_text}
\"\"\"

Extracted Details:
Role: {parsed_jd.role}
Company: {parsed_jd.company}
Tech Stack: {', '.join(parsed_jd.tech_stack)}

Live Market Intelligence & Interview Context:
\"\"\"
{context_str}
\"\"\"

Generate a comprehensive, highly accurate Interview Rubric.
Return strictly valid JSON matching this exact structure:
{{
  "roleOverview": "Summary of role expectations and target candidate profile",
  "keyTechnicalPillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
  "expectedInterviewTopics": [
    {{
      "category": "System Design / Data Structures / Core Tech",
      "difficulty": "Junior" | "Mid" | "Senior",
      "example_questions": [
        "Question 1",
        "Question 2",
        "Question 3"
      ]
    }}
  ]
}}
"""

    raw_json = call_gemini_api(prompt, json_mode=True, temperature=0.3)

    # Clean code fences
    clean_json = raw_json.strip()
    if clean_json.startswith("```json"):
        clean_json = clean_json[7:]
    if clean_json.startswith("```"):
        clean_json = clean_json[3:]
    if clean_json.endswith("```"):
        clean_json = clean_json[:-3]

    return InterviewRubric.model_validate_json(clean_json.strip())
