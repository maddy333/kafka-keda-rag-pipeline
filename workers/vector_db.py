import uuid
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from workers.config import settings

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Qdrant Vector DB client managing collection initialization and bulk vector upserts."""

    def __init__(self):
        logger.info("Initializing Qdrant client at %s:%d", settings.QDRANT_HOST, settings.QDRANT_PORT)
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.QDRANT_VECTOR_SIZE
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates Qdrant vector collection if missing."""
        try:
            collections = self.client.get_collections().collections
            existing_names = [c.name for c in collections]
            if self.collection_name not in existing_names:
                logger.info("Creating Qdrant collection: %s", self.collection_name)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_size,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.warning("Qdrant collection verification warning: %s", str(e))

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def upsert_chunks(self, chunks: List[Dict[str, Any]], vectors: List[List[float]]):
        """Bulk upserts chunk vectors and payload metadata into Qdrant with retry logic."""
        if not chunks or not vectors:
            return

        points = []
        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "doc_id": chunk["doc_id"],
                        "filename": chunk["filename"],
                        "chunk_index": chunk["chunk_index"],
                        "text": chunk["text"],
                        "char_start": chunk["char_start"],
                        "char_end": chunk["char_end"],
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        logger.info("Upserted %d vector points into Qdrant collection '%s'", len(points), self.collection_name)


qdrant_store = QdrantVectorStore()
