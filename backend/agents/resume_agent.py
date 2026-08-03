"""
Resume RAG Agent — answers questions based on resume PDFs.

Given a user question, retrieves relevant chunks from the vector store,
then uses LLM to generate a grounded answer.
"""
from typing import AsyncGenerator

from backend.config import SIMILARITY_THRESHOLD, TOP_K
from backend.rag.vector_store import search_similar
from backend.services.llm import stream_chat


RESUME_SYSTEM_PROMPT = """You are a professional resume assistant. Answer questions based on the provided resume excerpts.

Rules:
1. Answer in Chinese, using the same language as the question.
2. Use information from the provided context. Look broadly across all chunks — project experience may appear under "实习经验", "学术经历", "项目经历" or similar section headers. Search for specific project names, descriptions, and achievements.
3. Only if you've thoroughly checked ALL provided chunks and absolutely cannot find any relevant information, say "根据简历内容，没有找到相关信息".
4. Be comprehensive and accurate. Format key information clearly with bullet points.
5. When describing projects, include: project name, tech stack, responsibilities, and outcomes when available.
6. Do not fabricate any information not present in the context.
7. If asked to introduce the person, give a structured summary covering: education, skills, experience, and projects."""


async def answer_resume_question(
    question: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Answer a resume-related question using RAG + LLM.

    Yields SSE delta strings.
    """
    from backend.services.sse import sse_delta, sse_done, sse_error, sse_metadata

    # Step 1: Retrieve relevant chunks
    chunks = search_similar(question, top_k=TOP_K)

    # Check similarity threshold
    if not chunks or chunks[0]["similarity"] < SIMILARITY_THRESHOLD:
        yield sse_metadata({"mode": "resume", "sources": [], "similarity": 0})
        yield sse_delta("根据简历内容，没有找到足够相关的信息来回答您的问题。\n\n")
        yield sse_delta("建议：请尝试更具体的提问，或切换到搜索模式获取更广泛的信息。")
        yield sse_done()
        return

    # Build context from retrieved chunks
    context_parts: list[str] = []
    sources: list[dict] = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[来源{i}] (相似度: {chunk['similarity']:.2f})\n{chunk['content']}")
        sources.append({
            "source": chunk["metadata"]["source"],
            "similarity": chunk["similarity"],
        })

    context = "\n\n---\n\n".join(context_parts)

    # Send metadata
    yield sse_metadata({
        "mode": "resume",
        "sources": sources,
        "similarity": chunks[0]["similarity"],
    })

    # Step 2: Build messages and stream LLM response
    messages = [{"role": "system", "content": RESUME_SYSTEM_PROMPT}]

    # Add conversation history (last 6 messages for context)
    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": f"Context from resume(s):\n{context}\n\nQuestion: {question}\n\nPlease answer based on the context above.",
    })

    try:
        async for text in stream_chat(messages):
            yield sse_delta(text)
        yield sse_done()
    except Exception as e:
        yield sse_error(f"LLM error: {str(e)}")
