import logging
from minio import Minio
from google.cloud import storage as gcs_storage
from workers.config import settings

logger = logging.getLogger(__name__)


class WorkerStorageFetcher:
    """Document fetcher client reading raw bytes from GCS or MinIO."""

    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        if self.backend == "gcs":
            logger.info("Worker GCS Storage Client initialized for project: %s", settings.GCP_PROJECT_ID)
            self.gcs_client = gcs_storage.Client(project=settings.GCP_PROJECT_ID)
        else:
            logger.info("Worker MinIO Storage Client initialized at endpoint: %s", settings.MINIO_ENDPOINT)
            self.minio_client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )

    def fetch_document_text(self, bucket_name: str, object_key: str) -> str:
        """Downloads document bytes and decodes text content."""
        if self.backend == "gcs":
            bucket = self.gcs_client.bucket(bucket_name)
            blob = bucket.blob(object_key)
            data_bytes = blob.download_as_bytes()
        else:
            response = self.minio_client.get_object(bucket_name, object_key)
            try:
                data_bytes = response.read()
            finally:
                response.close()
                response.release_conn()

        try:
            return data_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback decoding for non-utf8 text documents
            return data_bytes.decode("latin-1")


worker_storage = WorkerStorageFetcher()
