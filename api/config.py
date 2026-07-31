import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    PROJECT_NAME: str = "distributed-rag-api"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Kafka Configurations
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_DOCUMENT_UPLOADED: str = "document-uploaded"
    
    # Object Storage Backend: "gcs" or "minio"
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
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = APISettings()
