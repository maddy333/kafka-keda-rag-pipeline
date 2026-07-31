import logging
from typing import List, Dict, Any
from workers.config import settings

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Smart text chunker with configurable size, overlap, and metadata extraction."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, doc_id: str, filename: str) -> List[Dict[str, Any]]:
        """Splits raw text string into chunks with character boundaries and metadata."""
        if not text or not text.strip():
            logger.warning("Empty text passed to chunker for doc_id: %s", doc_id)
            return []

        chunks = []
        start = 0
        text_length = len(text)
        chunk_idx = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            
            # Adjust to end of word if possible
            if end < text_length and not text[end].isspace():
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append({
                    "chunk_id": f"{doc_id}_chunk_{chunk_idx}",
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": chunk_idx,
                    "text": chunk_content,
                    "char_start": start,
                    "char_end": end,
                    "char_length": len(chunk_content),
                })
                chunk_idx += 1

            start = end - self.overlap if end < text_length else text_length

        logger.info("Generated %d chunks for document: %s", len(chunks), doc_id)
        return chunks


chunker_engine = SemanticChunker()
