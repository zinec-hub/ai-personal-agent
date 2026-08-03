"""
FastAPI application entry point.

Hosts the unified agent API, static frontend files, and manages
lifecycle events (vector store init, Cloudflare Tunnel).
"""
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.config import (
    HOST,
    PORT,
    CLOUDFLARE_AUTO_START,
    FRONTEND_DIST,
    PDF_DIR,
    MARKDOWN_DIR,
    TOP_K,
)
from backend.rag.vector_store import build_index, needs_rebuild, search_similar, get_stats
from backend.agents.unified_agent import route_and_answer
from backend.agents.resume_agent import answer_resume_question
from backend.agents.search_agent import answer_search_question


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None
    mode: str | None = None  # "auto" | "resume" | "search"


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = TOP_K


# --- Lifecycle ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("\n" + "=" * 60)
    print("  AI Personal Agent — Starting up...")
    print("=" * 60)

    # Initialize vector store
    print(f"\n[rag] Checking data dir: {MARKDOWN_DIR}")
    if needs_rebuild():
        print("[rag] Building vector index (markdown only)...")
        count = build_index(force=True)
        print(f"[rag] Index built: {count} chunks")
    else:
        stats = get_stats()
        print(f"[rag] Using existing index: {stats['total_chunks']} chunks from {stats['files']}")

    # Start Cloudflare Tunnel (if configured)
    if CLOUDFLARE_AUTO_START:
        print("\n[cloudflared] Starting tunnel...")
        from backend.utils.cloudflare_tunnel import start_tunnel
        # Run in thread to not block startup
        import threading
        threading.Thread(
            target=start_tunnel,
            args=(PORT,),
            daemon=True,
        ).start()

    print(f"\n[server] Listening on http://{HOST}:{PORT}")
    print("=" * 60 + "\n")

    yield

    # Shutdown
    print("\n[server] Shutting down...")
    from backend.utils.cloudflare_tunnel import stop_tunnel
    stop_tunnel()


# --- App ---

app = FastAPI(
    title="AI Personal Agent",
    description="AI-powered personal resume agent with RAG and web search",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Routes ---


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    stats = get_stats()
    return {
        "status": "ok",
        "rag_chunks": stats["total_chunks"],
        "files": stats["files"],
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint — streams SSE events.

    Supports three modes:
    - auto: automatically route to resume or search agent
    - resume: force resume RAG mode
    - search: force web search mode
    """
    mode = request.mode or "auto"

    if mode == "resume":
        generator = answer_resume_question(request.message, request.history)
    elif mode == "search":
        generator = answer_search_question(request.message, request.history)
    else:
        generator = route_and_answer(request.message, request.history)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/rag/query")
async def rag_query(request: RAGQueryRequest):
    """Direct RAG query (no LLM) — returns raw search results."""
    chunks = search_similar(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "results": chunks,
        "count": len(chunks),
    }


@app.get("/api/rag/stats")
async def rag_stats():
    """Get RAG vector store statistics."""
    return get_stats()


@app.post("/api/rag/rebuild")
async def rag_rebuild():
    """Force rebuild the vector index."""
    count = build_index(force=True)
    return {"status": "ok", "chunks_indexed": count}


# --- PDF Download ---


@app.get("/api/pdf/list")
async def pdf_list():
    """List available PDF resume files for download."""
    if not PDF_DIR.exists():
        return {"files": []}
    files = sorted(
        [f.name for f in PDF_DIR.iterdir() if f.suffix.lower() == ".pdf"]
    )
    return {"files": files}


@app.get("/api/pdf/download/{filename}")
async def pdf_download(filename: str):
    """Download a specific PDF resume file."""
    file_path = PDF_DIR / filename
    if not file_path.exists() or file_path.suffix.lower() != ".pdf":
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(
        str(file_path),
        media_type="application/pdf",
        filename=filename,
    )


# --- Static Frontend ---


@app.get("/api/config")
async def get_config():
    """Return public config for the frontend."""
    return {
        "appName": "AI Personal Agent",
        "welcomeMessage": "你好！我是周柄材的AI简历助手。你可以问我关于简历的问题，也可以问我任何其他问题。",
        "suggestions": [
            "周柄材的专业是什么？",
            "周柄材有什么项目经验",
            "周柄材掌握了哪些技术技能？",
            "请介绍一下这个人的教育背景",
            "今天有哪些科技新闻？",
        ],
    }


# Serve frontend static files and SPA fallback
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    # Mount specific asset directories to avoid conflict with root route
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str = ""):
        """Serve frontend SPA — fallback to index.html."""
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    @app.get("/")
    async def serve_root():
        """Serve frontend root."""
        return FileResponse(str(FRONTEND_DIST / "index.html"))


# --- Main ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
