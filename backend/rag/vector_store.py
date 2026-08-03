"""
ChromaDB vector store for RAG document retrieval.

Stores document chunks with metadata, supports similarity search.
"""
import hashlib
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import CHROMA_DIR, TOP_K, MARKDOWN_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from backend.rag.loader import load_all_chunks, get_all_file_list
from backend.rag.embeddings import embed_texts, embed_query


COLLECTION_NAME = "resume_chunks"


def _get_client() -> chromadb.PersistentClient:
    """Get or create the ChromaDB persistent client."""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_collection() -> chromadb.Collection:
    """Get or create the resume collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _make_chunk_id(filename: str, chunk_index: int) -> str:
    """Generate a deterministic chunk ID."""
    raw = f"{filename}::{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def build_index(force: bool = False) -> int:
    """
    Build/rebuild the vector index from all knowledge base chunks.

    Returns the total number of chunks indexed.
    """
    collection = _get_collection()

    # If not forced and collection already has data, skip
    if not force and collection.count() > 0:
        return collection.count()

    # Force rebuild: delete and recreate to ensure correct hnsw:space
    if force and collection.count() > 0:
        client = _get_client()
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        collection = _get_collection()

    chunks = load_all_chunks()
    total_chunks = len(chunks)

    if total_chunks == 0:
        return 0

    texts = [c["text"] for c in chunks]
    ids = [_make_chunk_id(c["source"] + c.get("type", ""), i) for i, c in enumerate(chunks)]
    metadatas = [
        {
            "source": c["source"],
            "chunk_index": i,
            "char_count": len(c["text"]),
            "chunk_type": c.get("type", "general"),
        }
        for i, c in enumerate(chunks)
    ]

    embeddings = embed_texts(texts)

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    # Persist document list for change detection
    _save_file_list()

    return total_chunks


def _compute_file_hash(filepath: str) -> str:
    """Compute MD5 hash of a file for change detection."""
    import hashlib
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except Exception:
        return "00000000000000000000000000000000"
    return h.hexdigest()


def _save_file_list():
    """Save current document file list with content hashes to detect changes."""
    import os
    from backend.config import MARKDOWN_DIR
    lines: list[str] = []
    for fname in get_all_file_list():
        # fname format: "markdown/filename.md"
        full_path = os.path.join(MARKDOWN_DIR.parent, fname)
        h = _compute_file_hash(full_path)
        lines.append(f"{fname}|{h}")
    list_path = CHROMA_DIR / ".file_list.txt"
    list_path.write_text("\n".join(lines), encoding="utf-8")


def _current_file_snapshot() -> dict[str, str]:
    """Return {filename: hash} for all current knowledge base files."""
    import os
    from backend.config import MARKDOWN_DIR
    snapshot: dict[str, str] = {}
    for fname in get_all_file_list():
        full_path = os.path.join(MARKDOWN_DIR.parent, fname)
        snapshot[fname] = _compute_file_hash(full_path)
    return snapshot


def needs_rebuild() -> bool:
    """
    Check if the vector index needs rebuilding.
    Detects: new files, deleted files, and content changes (via MD5 hash).
    """
    collection = _get_collection()
    if collection.count() == 0:
        return True

    list_path = CHROMA_DIR / ".file_list.txt"
    if not list_path.exists():
        return True

    # Parse stored snapshot
    stored: dict[str, str] = {}
    stored_text = list_path.read_text(encoding="utf-8").strip()
    if stored_text:
        for line in stored_text.split("\n"):
            parts = line.rsplit("|", 1)
            if len(parts) == 2:
                stored[parts[0]] = parts[1]

    # Compare with current snapshot
    current = _current_file_snapshot()
    if set(current.keys()) != set(stored.keys()):
        return True  # files added or removed

    for fname, chash in current.items():
        if stored.get(fname) != chash:
            return True  # content changed

    return False


def search_similar(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Search for chunks similar to the query.

    Returns list of {content, metadata, similarity}.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[dict] = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Cosine distance → similarity: 1 - distance (for normalized vectors)
            similarity = 1.0 - dist
            chunks.append({
                "content": doc,
                "metadata": meta,
                "similarity": round(similarity, 4),
            })

    return chunks


def get_stats() -> dict:
    """Return vector store statistics."""
    collection = _get_collection()
    return {
        "collection_name": COLLECTION_NAME,
        "total_chunks": collection.count(),
        "files": get_all_file_list(),
    }
