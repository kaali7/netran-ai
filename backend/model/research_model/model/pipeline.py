import logging
import os
import time
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
        output_dir: str | None = None,
        force_refresh: bool = False
    ) -> Stage1Output:
        """
        Executes the end-to-end Stage 1 pipeline.

        Steps:
        1. Check SQLite Cache (hash-based) unless force_refresh is True
        2. Parse JD metadata & form 3 search queries (Gemini)
        3. Execute multi-vector parallel web search on trusted domains (Tavily API)
        4. Synthesize context into structured JSON rubric (Gemini)
        5. Cache result & return Stage1Output with execution time telemetry
        """
        start_time = time.time()

        def notify(msg: str):
            logger.info(msg)
            if status_callback:
                status_callback(msg)

        if not force_refresh:
            notify("Checking cache for existing rubric...")
            cached_rubric = self.cache.get(jd_text)
            if cached_rubric:
                elapsed = round(time.time() - start_time, 3)
                notify(f"Loaded existing rubric from cache in {elapsed}s!")
                parsed_jd = ParsedJD(
                    role="Cached Target Profile",
                    company="Target Company",
                    target_seniority="Senior",
                    tech_stack=cached_rubric.keyTechnicalPillars,
                    search_queries=[]
                )
                output_obj = Stage1Output(
                    rubric=cached_rubric,
                    parsed_jd=parsed_jd,
                    search_context=[],
                    cached=True,
                    execution_time_seconds=elapsed
                )
                if output_dir:
                    self.save_artifacts(output_dir, output_obj)
                return output_obj

        notify("Parsing Job Description with Gemini (3-vector query formulation)...")
        parsed_jd = self.parser.parse(jd_text)

        notify(f"Searching web (Tavily Multi-Vector) for role: '{parsed_jd.role}'...")
        search_context = self.search_engine.search(parsed_jd.search_queries)

        notify(f"Found {len(search_context)} market intel snippets. Synthesizing Market & Role Rubric...")
        rubric = self.rubric_generator.generate(jd_text, parsed_jd, search_context)

        notify("Caching results in database...")
        self.cache.set(jd_text, rubric)

        elapsed = round(time.time() - start_time, 2)
        output_obj = Stage1Output(
            rubric=rubric,
            parsed_jd=parsed_jd,
            search_context=search_context,
            cached=False,
            execution_time_seconds=elapsed
        )

        if output_dir:
            self.save_artifacts(output_dir, output_obj)

        notify(f"Pipeline complete in {elapsed}s!")
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
    output_dir: str | None = None,
    force_refresh: bool = False
) -> Stage1Output:
    return Stage1Pipeline().run(
        jd_text=jd_text,
        status_callback=status_callback,
        output_dir=output_dir,
        force_refresh=force_refresh
    )

