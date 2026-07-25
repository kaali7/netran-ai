"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: pipeline.py
Description: Master Stage 1 pipeline execution module linking SQLite caching, JD parsing,
             Tavily market intelligence searching, and Gemini rubric synthesis.
"""

import os
import json
import logging
from typing import Callable, Optional
try:
    from .schemas import InterviewRubric, ParsedJD, Stage1Output
    from .cache import get_cached_rubric, set_cached_rubric
    from .jd_parser import parse_jd
    from .search_engine import search_market_intelligence
    from .rubric_generator import generate_rubric
except ImportError:
    try:
        from model.research_model.model.schemas import InterviewRubric, ParsedJD, Stage1Output
        from model.research_model.model.cache import get_cached_rubric, set_cached_rubric
        from model.research_model.model.jd_parser import parse_jd
        from model.research_model.model.search_engine import search_market_intelligence
        from model.research_model.model.rubric_generator import generate_rubric
    except ImportError:
        from schemas import InterviewRubric, ParsedJD, Stage1Output
        from cache import get_cached_rubric, set_cached_rubric
        from jd_parser import parse_jd
        from search_engine import search_market_intelligence
        from rubric_generator import generate_rubric

logger = logging.getLogger(__name__)

def run_pipeline(
    jd_text: str,
    status_callback: Optional[Callable[[str], None]] = None,
    output_dir: Optional[str] = None
) -> Stage1Output:
    """
    Executes the end-to-end JD Research & Market Intelligence pipeline.
    
    Steps:
    1. Check SQLite Cache (hash-based)
    2. Parse JD metadata & form search queries (Gemini)
    3. Execute live web search on trusted engineering domains (Tavily API)
    4. Synthesize context into structured JSON rubric (Gemini)
    5. Cache result & return Stage1Output
    """
    def notify(msg: str):
        logger.info(msg)
        if status_callback:
            status_callback(msg)

    notify("Checking cache for existing rubric...")
    cached_rubric = get_cached_rubric(jd_text)
    if cached_rubric:
        notify("Loaded existing rubric from cache!")
        # Fallback metadata for cached hit
        parsed_jd = ParsedJD(
            role="Cached Target Profile",
            company="Target Company",
            tech_stack=cached_rubric.keyTechnicalPillars,
            search_queries=[]
        )
        output_obj = Stage1Output(
            rubric=cached_rubric,
            parsed_jd=parsed_jd,
            search_context=[],
            cached=True
        )
        if output_dir:
            _save_artifacts(output_dir, output_obj)
        return output_obj

    notify("Parsing Job Description with Gemini...")
    parsed_jd = parse_jd(jd_text)

    notify(f"Searching web (Tavily) for role: '{parsed_jd.role}' at '{parsed_jd.company}'...")
    search_context = search_market_intelligence(parsed_jd.search_queries)

    notify(f"Found {len(search_context)} market intel sources. Generating assessment rubric...")
    rubric = generate_rubric(jd_text, parsed_jd, search_context)

    notify("Caching results in database...")
    set_cached_rubric(jd_text, rubric)

    output_obj = Stage1Output(
        rubric=rubric,
        parsed_jd=parsed_jd,
        search_context=search_context,
        cached=False
    )

    if output_dir:
        _save_artifacts(output_dir, output_obj)

    notify("Pipeline complete!")
    return output_obj

def _save_artifacts(output_dir: str, output_obj: Stage1Output):
    """Saves complete Stage1Output into a single consolidated stage1_output.json artifact."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        artifact_path = os.path.join(output_dir, "stage1_output.json")
        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(output_obj.model_dump_json(indent=2))
        logger.info(f"Stage 1 consolidated artifact saved cleanly to {artifact_path}")
    except Exception as e:
        logger.error(f"Failed to write output artifact to {output_dir}: {e}")

