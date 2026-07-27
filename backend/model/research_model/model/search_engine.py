import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

try:
    from .config import Stage1Config
except ImportError:
    try:
        from model.research_model.model.config import Stage1Config
    except ImportError:
        from config import Stage1Config

logger = logging.getLogger(__name__)

VECTOR_KEYS = ["technical", "market_salary", "hr_recruiter"]
VECTOR_LABELS = [
    "Technical Interview Questions",
    "Market & Salary Intelligence",
    "HR & Recruiter Screening Signals"
]


class MarketSearchEngine:
    """Class-based web intelligence search engine utilizing Tavily Search API."""

    def __init__(self, config: Stage1Config | None = None):
        self.config = config or Stage1Config.from_env()

    def _search_single_vector(self, client, query: str, label: str, vector_key: str | None = None) -> list[dict[str, str]]:
        """Executes a single search vector query with domain filtering and fallback handling."""
        trusted_domains = self.config.trusted_domains_by_vector.get(vector_key, self.config.trusted_domains) if vector_key else self.config.trusted_domains
        items_found = []
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                include_domains=trusted_domains,
                max_results=3
            )
            for item in response.get("results", []):
                items_found.append({
                    "vector": label,
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                })
        except Exception as query_err:
            logger.warning(f"Tavily search failed for vector '{label}' query '{query}': {query_err}")
            try:
                response = client.search(query=query, max_results=2)
                for item in response.get("results", []):
                    items_found.append({
                        "vector": label,
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", "")
                    })
            except Exception:
                pass
        return items_found

    def search(self, search_queries: list[str]) -> list[dict[str, str]]:
        """
        Executes parallel multi-vector web searches using Tavily Search API.
        Returns a list of dicts with vector label, title, url, and content.
        Gracefully falls back to empty list on failure or missing API key.
        """
        api_key = self.config.tavily_api_key

        if not api_key or api_key.startswith("tvly-YOUR"):
            logger.warning("Tavily API key not configured. Operating in Gemini-only fallback mode.")
            return []

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=api_key)

            queries_to_run = search_queries[:3]
            tasks = []

            with ThreadPoolExecutor(max_workers=min(3, max(1, len(queries_to_run)))) as executor:
                for idx, query in enumerate(queries_to_run):
                    label = VECTOR_LABELS[idx] if idx < len(VECTOR_LABELS) else f"Vector {idx+1}"
                    vector_key = VECTOR_KEYS[idx] if idx < len(VECTOR_KEYS) else None
                    tasks.append(executor.submit(self._search_single_vector, client, query, label, vector_key))

            results = []
            for future in tasks:
                results.extend(future.result())
            return results

        except Exception as e:
            logger.error(f"Failed to initialize or call Tavily API: {e}")
            return []


    async def execute_multi_vector_search(self, search_queries: list[str]) -> str:
        """
        Asynchronous wrapper executing multi-vector search and returning formatted text block for LLM synthesis.
        """
        results = self.search(search_queries)
        if not results:
            return "No web search context retrieved. Rely on detailed technical baseline knowledge."

        formatted_blocks = []
        for item in results:
            label = item.get("vector", "General Context")
            formatted_blocks.append(
                f"=== VECTOR: {label} ===\n"
                f"- Source: {item.get('title')} ({item.get('url')})\n"
                f"  Snippet: {item.get('content')}\n"
            )
        return "\n".join(formatted_blocks)


# Backward compatibility wrappers
def search_market_intelligence(search_queries: list[str]) -> list[dict[str, str]]:
    return MarketSearchEngine().search(search_queries)

