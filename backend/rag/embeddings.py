"""
Text embedding model using sentence-transformers.

Uses paraphrase-multilingual-MiniLM-L12-v2 (384-dim).
Loads from local cache first to avoid HF network issues.
"""
import os
from typing import List

from sentence_transformers import SentenceTransformer

from backend.config import EMBEDDING_MODEL, EMBEDDING_DIM

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model (singleton)."""
    global _model
    if _model is not None:
        return _model

    # Try local_files_only first to avoid HF timeout in China
    try:
        _model = SentenceTransformer(
            EMBEDDING_MODEL,
            local_files_only=True,
        )
    except Exception:
        # Fall back to downloading from HF mirror
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    model = get_embedding_model()
    embedding = model.encode([query], normalize_embeddings=True)
    return embedding[0].tolist()
