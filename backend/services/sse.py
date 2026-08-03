"""
SSE (Server-Sent Events) formatting utilities.
"""
import json


def sse_event(event: str, data: str | dict) -> str:
    """Format a single SSE event."""
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


def sse_delta(content: str) -> str:
    """Format a streaming text delta."""
    return sse_event("delta", {"content": content})


def sse_done() -> str:
    """Format a stream-complete event."""
    return sse_event("done", {"status": "complete"})


def sse_error(message: str) -> str:
    """Format an error event."""
    return sse_event("error", {"message": message})


def sse_metadata(meta: dict) -> str:
    """Format a metadata event (e.g., agent mode, sources)."""
    return sse_event("metadata", meta)
