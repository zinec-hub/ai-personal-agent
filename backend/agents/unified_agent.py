"""
Unified Agent — routes questions to the appropriate handler.

Two-tier routing strategy:
- FAQ chunk match + similarity >= 0.35 → resume (FAQ is pre-written, highly reliable)
- Non-FAQ chunk match + similarity >= 0.50 → resume (need higher confidence)
- Otherwise → search agent (SearXNG → DDG → LLM)

This prevents false positives like "科技新闻" matching "学术经历" chunks.
"""
from typing import AsyncGenerator

from backend.config import SIMILARITY_THRESHOLD
from backend.rag.vector_store import search_similar

# Higher threshold for non-FAQ chunks to avoid false routing
NON_FAQ_THRESHOLD = 0.50


async def route_and_answer(
    question: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Determine the question type and route to the right handler.

    Checks top-2 chunks. FAQ matches are trusted at standard threshold;
    non-FAQ matches require a higher bar to prevent misrouting.
    """
    from backend.services.sse import sse_metadata

    chunks = search_similar(question, top_k=2)
    if not chunks:
        # No matches at all → search
        yield sse_metadata({"mode": "search", "engine": "llm_direct", "reason": "no_rag_match"})
        from backend.agents.search_agent import answer_search_question
        async for event in answer_search_question(question, history):
            yield event
        return

    top = chunks[0]
    chunk_type = top["metadata"].get("chunk_type", "general")
    similarity = top["similarity"]

    # Decide based on chunk type
    if chunk_type == "faq":
        # FAQ entries contain pre-written Q&A — very reliable
        is_resume = similarity >= SIMILARITY_THRESHOLD
    else:
        # Non-FAQ chunks need higher confidence to avoid false positives
        is_resume = similarity >= NON_FAQ_THRESHOLD

    if is_resume:
        from backend.agents.resume_agent import answer_resume_question
        async for event in answer_resume_question(question, history):
            yield event
    else:
        yield sse_metadata({
            "mode": "search",
            "engine": "auto",
            "reason": f"low_similarity_{similarity:.2f}",
        })
        from backend.agents.search_agent import answer_search_question
        async for event in answer_search_question(question, history):
            yield event
