"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: pipeline.py
Description: Master class-based Stage1Pipeline orchestrator linking cache, parser, search, and rubric generator.
"""

import logging
import os
from collections.abc import Callable

try:
    from .cache import Stage1Cache
    from .config import Stage1Config
    from .jd_parser import JDParser
    from .rubric_generator import RubricGenerator
    from .schemas import InterviewRubric, ParsedJD, Stage1Output
    from .search_engine import MarketSearchEngine
except ImportError:
    try:
        from model.research_model.model.cache import Stage1Cache
        from model.research_model.model.config import Stage1Config
        from model.research_model.model.jd_parser import JDParser
        from model.research_model.model.rubric_generator import RubricGenerator
        from model.research_model.model.schemas import (
            InterviewRubric,
            ParsedJD,
            Stage1Output,
        )
        from model.research_model.model.search_engine import MarketSearchEngine
    except ImportError:
        from cache import Stage1Cache
        from config import Stage1Config
        from jd_parser import JDParser
        from rubric_generator import RubricGenerator
        from schemas import ParsedJD, Stage1Output
        from search_engine import MarketSearchEngine

logger = logging.getLogger(__name__)


class Stage1Pipeline:
    """Master pipeline execution class for Stage 1 (Research & Rubric Synthesis)."""

    def __init__(self, config: Stage1Config | None = None):
        self.config = config or Stage1Config.from_env()
        self.cache = Stage1Cache()
        self.parser = JDParser()
        self.search_engine = MarketSearchEngine(self.config)
        self.rubric_generator = RubricGenerator()

    def run(
        self,
        jd_text: str,
        status_callback: Callable[[str], None] | None = None,
        output_dir: str | None = None
    ) -> Stage1Output:
        """
        Executes the end-to-end Stage 1 pipeline.

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
        cached_rubric = self.cache.get(jd_text)
        if cached_rubric:
            notify("Loaded existing rubric from cache!")
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
                self.save_artifacts(output_dir, output_obj)
            return output_obj

        notify("Parsing Job Description with Gemini...")
        parsed_jd = self.parser.parse(jd_text)

        notify(f"Searching web (Tavily) for role: '{parsed_jd.role}' at '{parsed_jd.company}'...")
        search_context = self.search_engine.search(parsed_jd.search_queries)

        notify(f"Found {len(search_context)} market intel sources. Generating assessment rubric...")
        rubric = self.rubric_generator.generate(jd_text, parsed_jd, search_context)

        notify("Caching results in database...")
        self.cache.set(jd_text, rubric)

        output_obj = Stage1Output(
            rubric=rubric,
            parsed_jd=parsed_jd,
            search_context=search_context,
            cached=False
        )

        if output_dir:
            self.save_artifacts(output_dir, output_obj)

        notify("Pipeline complete!")
        return output_obj

    @staticmethod
    def save_artifacts(output_target: str, output_obj: Stage1Output):
        """Saves Stage1Output into a single JSON file named with session name or target path."""
        try:
            if output_target.lower().endswith(".json"):
                artifact_path = output_target
            elif os.path.isdir(output_target):
                artifact_path = os.path.join(output_target, "stage1_output.json")
            else:
                artifact_path = f"{output_target}.json"

            parent_dir = os.path.dirname(os.path.abspath(artifact_path))
            os.makedirs(parent_dir, exist_ok=True)

            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(output_obj.model_dump_json(indent=2))
            logger.info(f"Stage 1 JSON artifact saved cleanly to {artifact_path}")
        except Exception as e:
            logger.error(f"Failed to write output artifact to {output_target}: {e}")


# Backward compatibility pipeline function wrapper
def run_pipeline(
    jd_text: str,
    status_callback: Callable[[str], None] | None = None,
    output_dir: str | None = None
) -> Stage1Output:
    return Stage1Pipeline().run(jd_text, status_callback=status_callback, output_dir=output_dir)
