import io
import logging
from typing import Tuple
from minio import Minio
from google.cloud import storage as gcs_storage
from api.config import settings

logger = logging.getLogger(__name__)


class ObjectStorageClient:
    """Unified Object Storage Client supporting MinIO and Google Cloud Storage (GCS)."""

    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        if self.backend == "gcs":
            logger.info("Initializing GCP Cloud Storage client for project: %s", settings.GCP_PROJECT_ID)
            self.gcs_client = gcs_storage.Client(project=settings.GCP_PROJECT_ID)
            self.bucket_name = settings.GCS_BUCKET_NAME
        else:
            logger.info("Initializing MinIO client at endpoint: %s", settings.MINIO_ENDPOINT)
            self.minio_client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            self.bucket_name = settings.MINIO_BUCKET_NAME
            self._ensure_minio_bucket()

    def _ensure_minio_bucket(self):
        """Creates the MinIO bucket if it does not exist."""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info("Created MinIO bucket: %s", self.bucket_name)
        except Exception as e:
            logger.warning("MinIO bucket initialization check failed: %s", str(e))

    def upload_bytes(
        self, object_key: str, data: bytes, content_type: str
    ) -> Tuple[str, str]:
        """Uploads byte data to object storage and returns (bucket_name, object_key)."""
        data_stream = io.BytesIO(data)
        data_length = len(data)

        if self.backend == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(object_key)
            blob.upload_from_file(data_stream, content_type=content_type, size=data_length)
            logger.info("Successfully uploaded object %s to GCS bucket %s", object_key, self.bucket_name)
            return self.bucket_name, object_key
        else:
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=data_stream,
                length=data_length,
                content_type=content_type,
            )
            logger.info("Successfully uploaded object %s to MinIO bucket %s", object_key, self.bucket_name)
            return self.bucket_name, object_key

    def check_health(self) -> bool:
        """Health probe check for storage connectivity."""
        try:
            if self.backend == "gcs":
                self.gcs_client.get_bucket(self.bucket_name)
            else:
                self.minio_client.bucket_exists(self.bucket_name)
            return True
        except Exception as e:
            logger.error("Storage health check failed: %s", str(e))
            return False


storage_client = ObjectStorageClient()
