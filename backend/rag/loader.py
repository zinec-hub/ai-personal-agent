"""
Document loader: PDF (with OCR) + Markdown files.

Uses PyMuPDF for PDF text extraction and RapidOCR for scanned/image-based PDFs.
Loads .md files as plain text.
"""
import os
from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from backend.config import PDF_DIR, MARKDOWN_DIR, CHUNK_SIZE, CHUNK_OVERLAP


# OCR engine singleton
_ocr = None


def _init_ocr_engine():
    """Lazy-init the RapidOCR engine (ONNX Runtime)."""
    global _ocr
    if _ocr is not None:
        return _ocr
    try:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    except Exception:
        _ocr = None  # OCR unavailable
    return _ocr


def _extract_text_with_ocr(pdf_path: Path) -> str:
    """
    Extract text from a scanned/image-based PDF using RapidOCR.
    Renders each page as an image, then runs OCR.
    """
    ocr = _init_ocr_engine()
    if ocr is None:
        return ""

    doc = fitz.open(str(pdf_path))
    all_text: list[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page to image at 2x resolution for better OCR
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")

        result, _ = ocr(img_bytes)
        if result:
            page_text = " ".join(item[1] for item in result)
            all_text.append(page_text)

    doc.close()
    return "\n\n".join(all_text)


def _extract_text_native(pdf_path: Path) -> str:
    """Extract text directly from PDF (for text-based PDFs)."""
    doc = fitz.open(str(pdf_path))
    all_text: list[str] = []

    for page in doc:
        text = page.get_text()
        if text.strip():
            all_text.append(text)

    doc.close()
    return "\n\n".join(all_text)


def load_pdf(pdf_path: Path) -> str:
    """
    Load a single PDF file using OCR (RapidOCR) for reliable Chinese text extraction.
    Renders each page to an image and runs OCR to avoid encoding issues.
    """
    text = _extract_text_with_ocr(pdf_path)
    if not text.strip():
        # Fallback to native extraction only if OCR produced nothing
        text = _extract_text_native(pdf_path)
    return text


def load_all_pdfs(pdf_dir: Path | None = None) -> dict[str, str]:
    """
    Load all PDFs from the pdf directory.

    Returns a dict: {filename: full_text}
    """
    if pdf_dir is None:
        pdf_dir = PDF_DIR

    if not pdf_dir.exists():
        return {}

    result: dict[str, str] = {}
    for f in pdf_dir.iterdir():
        if f.suffix.lower() == ".pdf":
            text = load_pdf(f)
            if text.strip():
                result[f.name] = text
    return result


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split plain text into overlapping chunks by paragraph and sentence boundaries.
    Used for non-markdown content (e.g., OCR'd PDFs).
    """
    paragraphs = text.split("\n\n")
    chunks: list[str] = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            chunks.append(para)
            continue
        sentences = _split_sentences(para)
        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= chunk_size:
                current += sent
            else:
                if current.strip():
                    chunks.append(current.strip())
                if len(sent) > chunk_size:
                    for i in range(0, len(sent), chunk_size - overlap):
                        chunks.append(sent[i:i + chunk_size])
                    current = ""
                else:
                    current = sent
        if current.strip():
            chunks.append(current.strip())

    if overlap > 0:
        overlapped: list[str] = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                prev_tail = chunks[i - 1][-overlap:] if len(chunks[i - 1]) > overlap else chunks[i - 1]
                chunk = prev_tail + "\n" + chunk
            overlapped.append(chunk)
        chunks = overlapped

    return chunks


def chunk_markdown(text: str, max_chunk: int = 800, overlap: int = 80) -> list[str]:
    """
    Markdown-aware chunking: splits by ## headings, preserves section context,
    and for large sections splits by sub-boundaries (### headings, **project** markers).

    Each chunk includes its section path as a header for LLM context.
    """
    import re
    chunks: list[str] = []

    # Step 1: Split by ## headings (top-level sections)
    sections = re.split(r'\n(?=## )', text)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract the ## heading line
        lines = section.split('\n', 1)
        heading = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        if not body:
            continue

        # Step 2: For "项目经历" section, split by individual projects
        if '项目经历' in heading:
            _chunk_project_section(heading, body, max_chunk, overlap, chunks)
        # Step 3: For other sections, split by ### sub-headings
        elif '###' in body:
            _chunk_with_subheadings(heading, body, max_chunk, overlap, chunks)
        else:
            _chunk_simple_section(heading, body, max_chunk, overlap, chunks)

    return chunks


def _chunk_project_section(heading: str, body: str, max_chunk: int, overlap: int, chunks: list[str]):
    """Split the project section by company/role and individual projects."""
    import re

    # Split by ### (company/role headers)
    parts = re.split(r'\n(?=### )', body)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        lines = part.split('\n', 1)
        sub_heading = lines[0].strip()
        sub_body = lines[1].strip() if len(lines) > 1 else ""

        if not sub_body:
            continue

        context = f"{heading} > {sub_heading}"

        # Try to split by **项目X** markers
        project_parts = re.split(r'\n(\*\*项目[一二三四五六七八九十\d]+[：:].*?\*\*)', sub_body)

        if len(project_parts) > 1:
            # Has project markers — split each project into its own chunk(s)
            current_proj = ""
            current_header = ""
            for i, piece in enumerate(project_parts):
                piece = piece.strip()
                if not piece:
                    continue
                if re.match(r'\*\*项目[一二三四五六七八九十\d]+[：:]', piece):
                    # This is a project title
                    if current_proj:
                        _emit_chunks(context, current_header, current_proj, max_chunk, overlap, chunks)
                    current_header = piece
                    current_proj = ""
                else:
                    current_proj += "\n" + piece if current_proj else piece
            # Last project
            if current_proj:
                _emit_chunks(context, current_header, current_proj, max_chunk, overlap, chunks)
        else:
            # No project markers — treat as one block
            _emit_chunks(context, "", sub_body, max_chunk, overlap, chunks)


def _chunk_with_subheadings(heading: str, body: str, max_chunk: int, overlap: int, chunks: list[str]):
    """Split by ### sub-headings within a section."""
    import re
    parts = re.split(r'\n(?=### )', body)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n', 1)
        sub_heading = lines[0].strip() if lines[0].startswith('###') else ""
        sub_body = lines[1].strip() if len(lines) > 1 and sub_heading else part

        context = f"{heading} > {sub_heading}" if sub_heading else heading
        _emit_chunks(context, "", sub_body, max_chunk, overlap, chunks)


def _chunk_simple_section(heading: str, body: str, max_chunk: int, overlap: int, chunks: list[str]):
    """Chunk a simple section (no sub-headings)."""
    _emit_chunks(heading, "", body, max_chunk, overlap, chunks)


def _emit_chunks(context: str, sub_title: str, body: str, max_chunk: int, overlap: int, chunks: list[str]):
    """
    Emit one or more chunks from a content block, each prefixed with context.
    For bullet-point sections (like 专业技能), keep each major item group together.
    """
    header_block = f"[{context}]"
    if sub_title:
        header_block += f"\n{sub_title}"
    header_block += "\n"

    # If content fits in one chunk, keep it whole
    if len(header_block) + len(body) <= max_chunk:
        chunks.append(header_block + body)
        return

    # Split by double newlines (logical paragraph boundaries)
    paragraphs = body.split('\n\n')
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        candidate = current + ("\n\n" if current else "") + para
        if len(header_block) + len(candidate) <= max_chunk:
            current = candidate
        else:
            if current:
                chunks.append(header_block + current)
            # If single paragraph is too long, split it
            if len(header_block) + len(para) > max_chunk:
                _split_long_text(header_block, para, max_chunk, overlap, chunks)
                current = ""
            else:
                current = para
    if current:
        chunks.append(header_block + current)


def _split_long_text(header: str, text: str, max_chunk: int, overlap: int, chunks: list[str]):
    """Split an overly long text block by sentence boundaries."""
    sentences = _split_sentences(text)
    current = ""
    limit = max_chunk - len(header)
    for sent in sentences:
        if len(current) + len(sent) <= limit:
            current += sent
        else:
            if current.strip():
                chunks.append(header + current.strip())
            if len(sent) > limit:
                # Hard split by character
                for i in range(0, len(sent), limit - overlap):
                    chunks.append(header + sent[i:i + limit])
                current = ""
            else:
                current = sent
    if current.strip():
        chunks.append(header + current.strip())


def _split_sentences(text: str) -> list[str]:
    """Split text by Chinese/English sentence boundaries."""
    import re
    pattern = r'(?<=[。！？\.\!\?\n])\s*'
    parts = re.split(pattern, text)
    result: list[str] = []
    buf = ""
    for part in parts:
        buf += part
        if re.search(r'[。！？\.\!\?]$', buf) or len(buf) > 200:
            result.append(buf)
            buf = ""
    if buf.strip():
        result.append(buf)
    return result if result else [text]


def load_markdown(md_path: Path) -> str:
    """Load a single Markdown file as plain text."""
    return md_path.read_text(encoding="utf-8")


def load_all_markdowns(md_dir: Path | None = None) -> dict[str, str]:
    """
    Load all Markdown files from the markdown directory.

    Returns a dict: {filename: full_text}
    """
    if md_dir is None:
        md_dir = MARKDOWN_DIR

    if not md_dir.exists():
        return {}

    result: dict[str, str] = {}
    for f in md_dir.iterdir():
        if f.suffix.lower() == ".md":
            text = load_markdown(f)
            if text.strip():
                result[f.name] = text
    return result


def load_all_documents() -> dict[str, str]:
    """
    Load all documents from the Markdown directory only.

    Returns a dict: {filename: full_text}
    """
    return load_all_markdowns(MARKDOWN_DIR)


def load_metadata() -> dict:
    """Load resume_metadata.json with structured data and FAQs."""
    import json
    meta_path = MARKDOWN_DIR / "resume_metadata.json"
    if not meta_path.exists():
        return {}
    with open(meta_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_all_chunks() -> list[dict]:
    """
    Load all knowledge-base chunks with type tags.

    Returns list of {text, type, source}.
    Types: faq, basic_info, education, project, skill, academic, self_eval
    """
    all_chunks: list[dict] = []

    # 1. FAQ chunks (highest priority — exact question is the chunk text)
    faq_chunks = _load_faq_chunks()
    all_chunks.extend(faq_chunks)

    # 2. Knowledge base documents from markdown
    docs = load_all_markdowns(MARKDOWN_DIR)
    for filename, text in docs.items():
        md_chunks = _chunk_markdown_with_types(text, filename)
        all_chunks.extend(md_chunks)

    return all_chunks


def _load_faq_chunks() -> list[dict]:
    """Load FAQ entries as high-priority retrieval chunks."""
    meta = load_metadata()
    faqs = meta.get("faq", [])
    chunks: list[dict] = []
    for entry in faqs:
        chunks.append({
            "text": f"[FAQ] Q: {entry['q']}\nA: {entry['a']}",
            "type": "faq",
            "source": "resume_metadata.json",
        })
    return chunks


def _chunk_markdown_with_types(text: str, source: str) -> list[dict]:
    """
    Chunk markdown and tag each chunk with its content type.
    """
    import re
    chunks: list[dict] = []

    # Split by ## headings
    sections = re.split(r'\n(?=## )', text)

    # Section → type mapping
    type_map = {
        "基本信息": "basic_info",
        "教育经历": "education",
        "项目经历": "project",
        "专业技能": "skill",
        "学术经历": "academic",
        "个人项目": "project",
        "自我评价": "self_eval",
    }

    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split('\n', 1)
        heading = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        if not body:
            continue

        # Determine chunk type from heading
        chunk_type = "general"
        for key, val in type_map.items():
            if key in heading:
                chunk_type = val
                break

        # Use appropriate chunking strategy
        if '项目经历' in heading:
            raw = chunk_markdown(text)
            # Filter to only this section's chunks
            for c in raw:
                if heading in c:
                    chunks.append({"text": c, "type": chunk_type, "source": source})
        elif '###' in body:
            for c in _chunk_with_subheadings_raw(heading, body, 800, 80):
                chunks.append({"text": c, "type": chunk_type, "source": source})
        else:
            for c in _chunk_simple_section_raw(heading, body, 800, 80):
                chunks.append({"text": c, "type": chunk_type, "source": source})

    return chunks


def _chunk_with_subheadings_raw(heading: str, body: str, max_chunk: int, overlap: int) -> list[str]:
    """Split by ###, return raw strings."""
    import re
    chunks: list[str] = []
    parts = re.split(r'\n(?=### )', body)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n', 1)
        sub_heading = lines[0].strip() if lines[0].startswith('###') else ""
        sub_body = lines[1].strip() if len(lines) > 1 and sub_heading else part
        context = f"{heading} > {sub_heading}" if sub_heading else heading
        _emit_chunks(context, "", sub_body, max_chunk, overlap, chunks)
    return chunks


def _chunk_simple_section_raw(heading: str, body: str, max_chunk: int, overlap: int) -> list[str]:
    """Chunk a simple section, return raw strings."""
    chunks: list[str] = []
    _emit_chunks(heading, "", body, max_chunk, overlap, chunks)
    return chunks


def get_pdf_file_list(pdf_dir: Path | None = None) -> list[str]:
    """Get list of PDF filenames for change detection."""
    if pdf_dir is None:
        pdf_dir = PDF_DIR
    if not pdf_dir.exists():
        return []
    return sorted(f.name for f in pdf_dir.iterdir() if f.suffix.lower() == ".pdf")


def get_all_file_list() -> list[str]:
    """Get list of all knowledge base files for change detection."""
    files: list[str] = []
    d = MARKDOWN_DIR
    if d.exists():
        for f in d.iterdir():
            if f.suffix.lower() in (".md", ".json"):
                files.append(f"{d.name}/{f.name}")
    return sorted(files)
