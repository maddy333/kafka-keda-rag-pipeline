from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    WORKER_NAME: str = "distributed-rag-worker"
    LOG_LEVEL: str = "INFO"
    
    # Kafka Configurations
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP_ID: str = "rag-worker-group"
    KAFKA_TOPIC_DOCUMENT_UPLOADED: str = "document-uploaded"
    KAFKA_TOPIC_DLQ: str = "document-dlq"
    
    # Storage Backend
    STORAGE_BACKEND: Literal["gcs", "minio"] = "minio"
    
    # MinIO Configurations
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "raw-documents"
    
    # GCP GCS Configurations
    GCP_PROJECT_ID: str = "distributed-rag-gcp"
    GCS_BUCKET_NAME: str = "distributed-rag-raw-documents"
    
    # Qdrant Configurations
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "rag_documents"
    QDRANT_VECTOR_SIZE: int = 384  # Matches sentence-transformers/all-MiniLM-L6-v2
    
    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chunker Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Retry & DLQ settings
    MAX_RETRY_ATTEMPTS: int = 3
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = WorkerSettings()
