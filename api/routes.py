import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from api.config import settings
from api.schemas import (
    DocumentUploadResponse,
    IngestionStatusResponse,
    DocumentEventMessage,
    HealthCheckResponse,
)
from api.storage import storage_client
from api.kafka_producer import kafka_producer

router = APIRouter(prefix="/v1")

# In-memory status tracker for quick metadata lookup
doc_status_db = {}


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload document for distributed RAG ingestion",
)
async def upload_document(file: UploadFile = File(...)):
    """Validates file upload, streams to object storage, and publishes Kafka event."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    doc_id = str(uuid.uuid4())
    object_key = f"documents/{doc_id}/{file.filename}"

    try:
        bucket_name, key = storage_client.upload_bytes(
            object_key=object_key,
            data=contents,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload document to storage: {str(e)}"
        )

    event_payload = DocumentEventMessage(
        document_id=doc_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        storage_backend=settings.STORAGE_BACKEND,
        bucket_name=bucket_name,
        object_key=key,
        metadata={"uploaded_by": "api-gateway"},
    )

    published = await kafka_producer.send_document_event(event_payload)
    if not published:
        raise HTTPException(
            status_code=500, detail="Failed to publish document event to Kafka pipeline"
        )

    response_data = DocumentUploadResponse(
        document_id=doc_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        storage_path=f"{bucket_name}/{key}",
        status="PENDING",
    )

    doc_status_db[doc_id] = {
        "document_id": doc_id,
        "status": "PENDING",
        "filename": file.filename,
        "storage_path": f"{bucket_name}/{key}",
        "processed_chunks": 0,
        "error_message": None,
        "created_at": datetime.utcnow(),
    }

    return response_data


@router.get(
    "/documents/{doc_id}/status",
    response_model=IngestionStatusResponse,
    summary="Get document processing status",
)
async def get_document_status(doc_id: str):
    """Retrieves current processing status of a document."""
    if doc_id not in doc_status_db:
        raise HTTPException(status_code=404, detail="Document ID not found")
    return doc_status_db[doc_id]


@router.get("/healthz", response_model=HealthCheckResponse, summary="Liveness Probe")
async def healthz():
    """Liveness health probe."""
    return HealthCheckResponse(
        status="OK",
        service=settings.PROJECT_NAME,
        dependencies={"storage": "OK", "kafka": "OK"},
    )


@router.get("/readyz", response_model=HealthCheckResponse, summary="Readiness Probe")
async def readyz():
    """Readiness probe checking storage and kafka dependencies."""
    storage_ok = storage_client.check_health()
    kafka_ok = await kafka_producer.check_health()

    status_str = "OK" if (storage_ok and kafka_ok) else "DEGRADED"

    return HealthCheckResponse(
        status=status_str,
        service=settings.PROJECT_NAME,
        dependencies={
            "storage": "HEALTHY" if storage_ok else "UNHEALTHY",
            "kafka": "HEALTHY" if kafka_ok else "UNHEALTHY",
        },
    )
