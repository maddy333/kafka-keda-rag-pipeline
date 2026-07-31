import logging
from typing import List
from sentence_transformers import SentenceTransformer
from workers.config import settings

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Local embedding generator using Hugging Face sentence-transformers."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        logger.info("Loading sentence-transformer model: %s", model_name)
        self.model = SentenceTransformer(model_name)
        self.vector_dimension = self.model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded. Dimension: %d", self.vector_dimension)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a list of text strings."""
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist()


embedding_pipeline = EmbeddingPipeline()
