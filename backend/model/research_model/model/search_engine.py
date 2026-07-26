"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: search_engine.py
Description: Class-based Tavily Search API client for querying web intelligence from trusted domains.
"""

import logging
from typing import List, Dict, Optional

try:
    from .config import Stage1Config
except ImportError:
    try:
        from model.research_model.model.config import Stage1Config
    except ImportError:
        from config import Stage1Config

logger = logging.getLogger(__name__)


class MarketSearchEngine:
    """Class-based web intelligence search engine utilizing Tavily Search API."""

    def __init__(self, config: Optional[Stage1Config] = None):
        self.config = config or Stage1Config.from_env()

    def search(self, search_queries: List[str]) -> List[Dict[str, str]]:
        """
        Executes web searches using Tavily Search API for live market intelligence.
        Returns a list of dicts with title, url, and content.
        Gracefully falls back to empty list on failure or missing API key.
        """
        api_key = self.config.tavily_api_key
        trusted_domains = self.config.trusted_domains

        if not api_key or api_key.startswith("tvly-YOUR"):
            logger.warning("Tavily API key not configured. Operating in Gemini-only fallback mode.")
            return []

        results = []
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=api_key)

            for query in search_queries[:3]:
                try:
                    response = client.search(
                        query=query,
                        search_depth="advanced",
                        include_domains=trusted_domains,
                        max_results=3
                    )
                    for item in response.get("results", []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "content": item.get("content", "")
                        })
                except Exception as query_err:
                    logger.warning(f"Tavily search failed for query '{query}': {query_err}")
                    try:
                        response = client.search(query=query, max_results=2)
                        for item in response.get("results", []):
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "content": item.get("content", "")
                            })
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to initialize or call Tavily API: {e}")
            return []

        return results


# Backward compatibility wrapper
def search_market_intelligence(search_queries: List[str]) -> List[Dict[str, str]]:
    return MarketSearchEngine().search(search_queries)
