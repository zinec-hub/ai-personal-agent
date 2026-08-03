"""
Search Agent — uses SearXNG (primary), DuckDuckGo (backup), or LLM (fallback)
to answer non-resume questions.
"""
import json
from typing import AsyncGenerator

import httpx

from backend.config import SEARXNG_URL
from backend.services.llm import stream_chat, chat_once

SEARCH_SYSTEM_PROMPT = """You are a helpful assistant. Answer the user's question based on the provided search results.

Rules:
1. Answer in Chinese. Provide comprehensive, well-structured responses.
2. Cite sources using [1], [2] notation when using information from search results.
3. If search results are insufficient, supplement with your knowledge but note this clearly.
4. Use bullet points and headings for readability when appropriate.
5. At the end, list all source URLs under "参考来源" (References) section."""


async def _search_searxng(query: str, timeout: float = 10.0) -> list[dict]:
    """Search via SearXNG API."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{SEARXNG_URL}/search",
                params={"q": query, "format": "json", "language": "zh-CN"},
            )
            if resp.status_code == 200:
                data = resp.json()
                results: list[dict] = []
                for r in data.get("results", [])[:8]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", "") or r.get("snippet", ""),
                    })
                return results
    except Exception:
        pass
    return []


async def _search_duckduckgo(query: str) -> list[dict]:
    """Search via DuckDuckGo (backup)."""
    try:
        from duckduckgo_search import DDGS
        results: list[dict] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return results
    except Exception:
        return []


def _format_search_results(results: list[dict]) -> str:
    """Format search results as context string."""
    if not results:
        return "No search results available."
    parts: list[str] = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"[{i}] {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Content: {r['snippet']}"
        )
    return "\n\n".join(parts)


async def answer_search_question(
    question: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Answer a general question using web search + LLM.

    Falls back: SearXNG → DuckDuckGo → LLM direct.

    Yields SSE delta strings.
    """
    from backend.services.sse import sse_delta, sse_done, sse_error, sse_metadata

    # Try SearXNG first
    yield sse_metadata({"mode": "search", "engine": "searxng"})
    results = await _search_searxng(question)

    # Fallback to DuckDuckGo
    if not results:
        yield sse_metadata({"mode": "search", "engine": "duckduckgo"})
        results = await _search_duckduckgo(question)

    # Build messages for LLM
    messages = [{"role": "system", "content": SEARCH_SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])

    if results:
        context = _format_search_results(results)
        sources = [{"title": r["title"], "url": r["url"]} for r in results]
        yield sse_metadata({"mode": "search", "engine": "llm_with_search", "sources": sources})
        messages.append({
            "role": "user",
            "content": f"Search results:\n{context}\n\nQuestion: {question}",
        })
    else:
        # LLM direct as last resort
        yield sse_metadata({"mode": "search", "engine": "llm_direct"})
        messages.append({
            "role": "user",
            "content": question,
        })

    try:
        async for text in stream_chat(messages):
            yield sse_delta(text)
        yield sse_done()
    except Exception as e:
        yield sse_error(f"Search/LLM error: {str(e)}")
