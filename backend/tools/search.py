"""Web search abstraction. Free DuckDuckGo is the default provider; Tavily/SerpAPI
are opt-in paid fallbacks used only when their API keys are configured."""

import logging
import random
import time

import httpx
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException

from backend.core.config import get_settings
from backend.graph.state import SearchResult

logger = logging.getLogger("deepresearch.tools.search")


async def search(query: str, max_results: int = 5) -> list[SearchResult]:
    settings = get_settings()

    if settings.search_provider == "tavily" and settings.tavily_api_key:
        return await _search_tavily(query, max_results, settings.tavily_api_key)
    if settings.search_provider == "serpapi" and settings.serpapi_api_key:
        return await _search_serpapi(query, max_results, settings.serpapi_api_key)
    return _search_duckduckgo(query, max_results)


def _search_duckduckgo(query: str, max_results: int) -> list[SearchResult]:
    # ponytail: sub-questions fan out concurrently and all hit DDG at once,
    # tripping its rate limiter almost every run. Jittered retry covers the
    # common transient case; a real fix would stagger/queue calls globally.
    hits = []
    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=max_results))
            break
        except RatelimitException:
            if attempt == 2:
                logger.warning("duckduckgo_rate_limited", extra={"query": query})
                return []
            time.sleep(2 * (attempt + 1) + random.random())
        except Exception:
            logger.exception("duckduckgo_search_failed", extra={"query": query})
            return []
    return [
        SearchResult(
            url=h.get("href", ""),
            title=h.get("title", ""),
            snippet=h.get("body", ""),
            raw_content=None,
            source_type="web",
        )
        for h in hits
    ]


async def _search_tavily(query: str, max_results: int, api_key: str) -> list[SearchResult]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": max_results},
        )
        resp.raise_for_status()
        data = resp.json()
    return [
        SearchResult(
            url=r.get("url", ""),
            title=r.get("title", ""),
            snippet=r.get("content", ""),
            raw_content=r.get("raw_content"),
            source_type="web",
        )
        for r in data.get("results", [])
    ]


async def _search_serpapi(query: str, max_results: int, api_key: str) -> list[SearchResult]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": api_key, "num": max_results},
        )
        resp.raise_for_status()
        data = resp.json()
    return [
        SearchResult(
            url=r.get("link", ""),
            title=r.get("title", ""),
            snippet=r.get("snippet", ""),
            raw_content=None,
            source_type="web",
        )
        for r in data.get("organic_results", [])[:max_results]
    ]
