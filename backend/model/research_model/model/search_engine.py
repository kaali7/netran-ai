"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: search_engine.py
Description: Integrates Tavily Search API to query live internet intelligence from trusted engineering
             domains (LeetCode, Glassdoor, GitHub, GeeksforGeeks, Reddit) with graceful fallback resilience.
"""

import logging
from typing import List, Dict
from model.config import TAVILY_API_KEY, TRUSTED_DOMAINS

logger = logging.getLogger(__name__)

def search_market_intelligence(search_queries: List[str]) -> List[Dict[str, str]]:
    """
    Executes web searches using Tavily Search API for live market intelligence.
    Returns a list of dicts with title, url, and content.
    Gracefully falls back to empty list on failure or missing API key.
    """
    if not TAVILY_API_KEY or TAVILY_API_KEY.startswith("tvly-YOUR"):
        logger.warning("Tavily API key not configured. Operating in Gemini-only fallback mode.")
        return []

    results = []
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        for query in search_queries[:3]:  # Execute up to top 3 queries
            try:
                response = client.search(
                    query=query,
                    search_depth="advanced",
                    include_domains=TRUSTED_DOMAINS,
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
                # Try without strict domain whitelist as fallback search
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
