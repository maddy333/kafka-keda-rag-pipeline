import os
import sys
import time
import requests
import uuid

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def generate_sample_document(index: int) -> bytes:
    content = f"""
    ===================================================
    DISTRIBUTED RAG PIPELINE LOAD TEST DOCUMENT #{index}
    DOCUMENT UUID: {uuid.uuid4()}
    TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}
    ===================================================

    SECTION 1: SYSTEM ARCHITECTURE & SCALABILITY
    The distributed Retrieval-Augmented Generation (RAG) pipeline ingests high-throughput document
    streams via FastAPI gateway endpoints, pushes event signals into Apache Kafka event brokers,
    and stores raw payloads inside Google Cloud Storage (GCS) or S3-compatible MinIO object buckets.

    SECTION 2: EVENT-DRIVEN AUTOSCALING WITH KEDA
    Kubernetes Event-driven Autoscaling (KEDA) continuously monitors topic consumer lag on Apache Kafka.
    When consumer lag exceeds the threshold (e.g. 10 messages), KEDA dynamically triggers pod autoscaling,
    spinning up worker replicas from 1 to N to maintain sub-second processing latency.

    SECTION 3: VECTOR DB UPSERT & DEAD-LETTER QUEUE (DLQ)
    Asynchronous workers fetch raw document text, execute semantic text chunking, compute 384-dimensional
    dense vector embeddings using Hugging Face sentence-transformers, and bulk upsert points into Qdrant.
    Any unparseable document or vector DB failure is safely isolated into the Dead-Letter Queue (DLQ).

    SECTION 4: GRAPHIFY AST ENGINE INTEGRATION
    The repository incorporates Graphify AST extraction powered by tree-sitter parsing and Leiden community
    clustering to enable deterministic code navigation across distributed microservice boundaries.
    """
    return content.strip().encode("utf-8")


def run_simulation(num_documents: int = 10):
    print(f"🚀 Starting load simulation: Uploading {num_documents} test documents to {API_BASE_URL}...")
    
    successful_uploads = []
    failed_uploads = 0

    for i in range(1, num_documents + 1):
        filename = f"sample_doc_{i}.txt"
        doc_bytes = generate_sample_document(i)

        files = {"file": (filename, doc_bytes, "text/plain")}
        try:
            res = requests.post(f"{API_BASE_URL}/v1/documents/upload", files=files, timeout=10)
            if res.status_code == 202:
                data = res.json()
                print(f"  [✓] [{i}/{num_documents}] Uploaded '{filename}' -> doc_id: {data['document_id']}")
                successful_uploads.append(data['document_id'])
            else:
                print(f"  [✗] [{i}/{num_documents}] Failed to upload '{filename}': HTTP {res.status_code} - {res.text}")
                failed_uploads += 1
        except Exception as e:
            print(f"  [✗] [{i}/{num_documents}] Exception uploading '{filename}': {str(e)}")
            failed_uploads += 1

        time.sleep(0.2)

    print("\n---------------------------------------------------")
    print(f"📊 Load Simulation Summary:")
    print(f"   Total Attempted: {num_documents}")
    print(f"   Successful:      {len(successful_uploads)}")
    print(f"   Failed:          {failed_uploads}")
    print("---------------------------------------------------")

    if successful_uploads:
        print("\n🔍 Checking status for first uploaded document...")
        test_id = successful_uploads[0]
        try:
            status_res = requests.get(f"{API_BASE_URL}/v1/documents/{test_id}/status")
            print(f"   Status Response: {status_res.json()}")
        except Exception as e:
            print(f"   Could not fetch status: {str(e)}")


if __name__ == "__main__":
    count = 10
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    run_simulation(count)
