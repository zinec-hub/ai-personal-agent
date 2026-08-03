"""
Configuration center — reads all settings from .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


# --- DeepSeek API ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

# --- SearXNG ---
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8080")

# --- Cloudflare Tunnel ---
CLOUDFLARE_AUTO_START = os.getenv("CLOUDFLARE_AUTO_START", "false").lower() == "true"

# --- Server ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# --- RAG ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 6
SIMILARITY_THRESHOLD = 0.35      # FAQ >= this → resume question
NON_FAQ_THRESHOLD = 0.50        # Non-FAQ >= this → resume question

# --- Paths ---
PDF_DIR = ROOT_DIR / "pdf"
MARKDOWN_DIR = ROOT_DIR / "markdown"
DATA_DIRS = [PDF_DIR, MARKDOWN_DIR]
CHROMA_DIR = ROOT_DIR / "chroma_db"
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

# --- Embedding model ---
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

# --- LLM ---
LLM_MAX_TOKENS = 16384
LLM_TEMPERATURE = 0.7
