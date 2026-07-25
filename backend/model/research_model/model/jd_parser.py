"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: jd_parser.py
Description: Evaluates raw Job Description (JD) text via Gemini 3.6 Flash to extract
             structured metadata (role, company, tech stack) and targeted web search queries.
"""

import json
import logging
try:
    from .schemas import ParsedJD
    from .gemini_client import call_gemini_api
except ImportError:
    try:
        from model.research_model.model.schemas import ParsedJD
        from model.research_model.model.gemini_client import call_gemini_api
    except ImportError:
        from schemas import ParsedJD
        from gemini_client import call_gemini_api

logger = logging.getLogger(__name__)

def parse_jd(jd_text: str) -> ParsedJD:
    """
    Parses raw JD text using Gemini to extract structured metadata and 2-3 search queries.
    
    Args:
        jd_text: Unformatted raw text of the job description.
        
    Returns:
        ParsedJD Pydantic object containing role, company, tech stack, and search queries.
    """
    prompt = f"""
Analyze the following Job Description (JD) text and extract:
1. Role title
2. Company name (if mentioned, otherwise "Target Company")
3. Core technical stack and skills
4. 2-3 specific search queries to find actual real-world interview questions and interview rubrics for this specific role and company on trusted engineering sites like Glassdoor, LeetCode, GitHub.

Job Description:
\"\"\"
{jd_text}
\"\"\"

Return strictly JSON matching this structure:
{{
  "role": "Role Title",
  "company": "Company Name",
  "tech_stack": ["tech1", "tech2"],
  "search_queries": ["query 1", "query 2"]
}}
"""

    raw_json = call_gemini_api(prompt, json_mode=True, temperature=0.2)
    
    # Strip markdown code fencing if model included it
    clean_json = raw_json.strip()
    if clean_json.startswith("```json"):
        clean_json = clean_json[7:]
    if clean_json.startswith("```"):
        clean_json = clean_json[3:]
    if clean_json.endswith("```"):
        clean_json = clean_json[:-3]
        
    return ParsedJD.model_validate_json(clean_json.strip())
