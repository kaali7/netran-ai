"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: pipeline.py
Description: Master Stage 1 pipeline execution module linking SQLite caching, JD parsing,
             Tavily market intelligence searching, and Gemini rubric synthesis.
"""

import logging
from typing import Callable, Optional
from model.schemas import InterviewRubric
from model.cache import get_cached_rubric, set_cached_rubric
from model.jd_parser import parse_jd
from model.search_engine import search_market_intelligence
from model.rubric_generator import generate_rubric

logger = logging.getLogger(__name__)

def run_pipeline(jd_text: str, status_callback: Optional[Callable[[str], None]] = None) -> InterviewRubric:
    """
    Executes the end-to-end JD Research & Market Intelligence pipeline.
    
    Steps:
    1. Check SQLite Cache (hash-based)
    2. Parse JD metadata & form search queries (Gemini)
    3. Execute live web search on trusted engineering domains (Tavily API)
    4. Synthesize context into structured JSON rubric (Gemini)
    5. Cache result & return
    """
    def notify(msg: str):
        logger.info(msg)
        if status_callback:
            status_callback(msg)

    notify("Checking cache for existing rubric...")
    cached_rubric = get_cached_rubric(jd_text)
    if cached_rubric:
        notify("Loaded existing rubric from cache!")
        return cached_rubric

    notify("Parsing Job Description with Gemini...")
    parsed_jd = parse_jd(jd_text)

    notify(f"Searching web (Tavily) for role: '{parsed_jd.role}' at '{parsed_jd.company}'...")
    search_context = search_market_intelligence(parsed_jd.search_queries)

    notify(f"Found {len(search_context)} market intel sources. Generating assessment rubric...")
    rubric = generate_rubric(jd_text, parsed_jd, search_context)

    notify("Caching results in database...")
    set_cached_rubric(jd_text, rubric)

    notify("Pipeline complete!")
    return rubric
