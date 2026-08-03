"""
DeepSeek LLM streaming client (OpenAI-compatible API).
"""
from typing import AsyncGenerator
from openai import AsyncOpenAI

from backend.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client


async def stream_chat(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream a chat completion from DeepSeek.

    Yields text deltas as they arrive.
    """
    client = _get_client()
    stream = await client.chat.completions.create(
        model=model or DEEPSEEK_MODEL,
        messages=messages,
        max_tokens=max_tokens or LLM_MAX_TOKENS,
        temperature=temperature or LLM_TEMPERATURE,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def chat_once(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Non-streaming chat completion. Returns the full response.
    """
    client = _get_client()
    response = await client.chat.completions.create(
        model=model or DEEPSEEK_MODEL,
        messages=messages,
        max_tokens=max_tokens or LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
        stream=False,
    )
    return response.choices[0].message.content or ""
