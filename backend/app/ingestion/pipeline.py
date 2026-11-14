"""Safe local document extraction, chunking and CPU embedding generation."""
from pathlib import Path
from typing import Iterable
from uuid import UUID, uuid5, NAMESPACE_URL
import re
from fastapi import HTTPException
from app.config import get_settings

_ALLOWED = {".pdf", ".docx", ".txt", ".md"}


def extract_pages(path: Path) -> list[tuple[int, str]]:
    suffix = path.suffix.lower()
    if suffix not in _ALLOWED:
        raise HTTPException(status_code=415, detail="Supported files: PDF, DOCX, TXT and Markdown")
    if suffix == ".pdf":
        import fitz
        with fitz.open(path) as pdf:
            return [(i + 1, page.get_text("text")) for i, page in enumerate(pdf)]
    if suffix == ".docx":
        from docx import Document
        doc = Document(path)
        return [(1, "\n".join(p.text for p in doc.paragraphs if p.text.strip()))]
    return [(1, path.read_text(encoding="utf-8", errors="replace"))]


def chunk_pages(pages: Iterable[tuple[int, str]], size: int = 1100, overlap: int = 160) -> list[dict]:
    chunks: list[dict] = []
    for page_number, text in pages:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            continue
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + size)
            if end < len(normalized):
                boundary = normalized.rfind(" ", start + size // 2, end)
                if boundary > start:
                    end = boundary
            content = normalized[start:end].strip()
            if content:
                chunks.append({"page": page_number, "text": content, "chunk_index": len(chunks)})
            if end >= len(normalized):
                break
            start = max(start + 1, end - overlap)
    return chunks


class EmbeddingService:
    def __init__(self) -> None:
        self._model = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=get_settings().embedding_model)
        return [vector.tolist() for vector in self._model.embed(texts)]


embedding_service = EmbeddingService()


def chunk_point_id(document_id: UUID, chunk_index: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"smartdoctor:{document_id}:{chunk_index}"))
