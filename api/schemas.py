from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique document ID (UUID)")
    filename: str = Field(..., description="Original name of uploaded document")
    content_type: str = Field(..., description="MIME type of document")
    size_bytes: int = Field(..., description="Size of uploaded document in bytes")
    storage_path: str = Field(..., description="Object storage key or URI")
    status: str = Field(default="PENDING", description="Processing status")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IngestionStatusResponse(BaseModel):
    document_id: str
    status: str
    filename: str
    storage_path: str
    processed_chunks: Optional[int] = 0
    error_message: Optional[str] = None
    created_at: datetime


class DocumentEventMessage(BaseModel):
    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_backend: str
    bucket_name: str
    object_key: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    dependencies: Dict[str, str]
