# Distributed RAG Pipeline (`distributed-rag-pipeline`)

A production-grade, 100% open-source, event-driven Retrieval-Augmented Generation (RAG) ingestion pipeline engineered for sub-second document indexing, high throughput event processing, and cloud-native Kubernetes scaling.

Built with **FastAPI**, **Apache Kafka**, **MinIO / Google Cloud Storage (GCS)**, **Qdrant Vector Engine**, **Hugging Face Sentence-Transformers**, **KEDA (Kubernetes Event-driven Autoscaling)**, and **Graphify** knowledge graph codebase mapping.

---

## 🏗️ System Architecture & Event Flow

```text
                  +-------------------------------------------------------------+
                  |                      CLIENT / SINK                          |
                  +-------------------------------------------------------------+
                                                 |
                                         POST /v1/documents/upload
                                                 v
                               +----------------------------------+
                               |    FastAPI Ingestion Gateway     |
                               |             (api/)               |
                               +----------------------------------+
                                  /                            \
                  1. Stream Raw Bytes                2. Publish Upload Event
                                /                                \
                               v                                  v
           +-----------------------+                    +-------------------+
           | Object Storage Layer  |                    |   Apache Kafka    |
           |  (GCP GCS / MinIO)    |                    |  Topic: document- |
           +-----------------------+                    |     uploaded      |
                       ^                                +-------------------+
                       |                                          |
               Fetch Document Text                                 | Consumer Lag
                       |                                          v
           +----------------------------------------------------------------+
           |                KEDA Worker Pod Pool (workers/)                 |
           |             [Scaled 1 -> N pods based on Kafka Lag]            |
           +----------------------------------------------------------------+
             /                     |                        \              \
      Semantic Chunking    Embedding Generation      Qdrant Bulk    On Failure
     (workers/chunker.py) (Sentence-Transformers)      Upserting        (DLQ)
             \                     |                        /              /
              v                    v                       v              v
           +------------------------------------------------+    +------------------+
           |         Qdrant Open-Source Vector DB           |    |   Apache Kafka   |
           |            (Collection: rag_documents)         |    |   Topic: doc-dlq |
           +------------------------------------------------+    +------------------+
```

---

## ⚡ Core Operational Deep-Dives

### 1. Event-Driven Scaling with KEDA (Kubernetes Event-driven Autoscaling)
- **Mechanics**: KEDA polls Apache Kafka consumer group lag on topic `document-uploaded` every 15 seconds via the `ScaledObject` controller (`deploy/helm/templates/scaledobject.yaml`).
- **Behavior**: When lag exceeds `10 messages per group`, KEDA instantly scales worker pods on Google Kubernetes Engine (GKE) up to a max of `10 replicas`. Once consumer lag drops back to zero, it scales worker pods down automatically to save compute costs.

### 2. Dead-Letter Queue (DLQ) Error Isolation
- **Resilience**: Transient storage or vector DB failures trigger exponential backoff retries (`tenacity` decorator in `vector_db.py`).
- **Isolation**: Unrecoverable failures (corrupted text, invalid JSON, or exhausted retries) are caught by `workers/dlq.py` and routed to the `document-dlq` topic with detailed exception metadata without crashing the worker pool.

### 3. Dual Object Storage Abstraction (GCP GCS & MinIO)
- Abstracted unified storage client (`api/storage.py` & `workers/storage.py`) supporting local S3-compatible MinIO for development and native **Google Cloud Storage (GCS)** for cloud deployments via **GCP Workload Identity**.

### 4. Graphify AST Knowledge Graph Navigation
- **Graphify Integration**: Uses `tree-sitter` AST parsing and **Leiden community clustering** configured in `.graphify/config.json` to generate deterministic structural maps (`graphify-out/`). This enables AI coding agents to navigate function definitions, class relationships, and architectural boundaries without brute-force grep or token bloat.

---

## 📂 Repository Structure

```
distributed-rag-pipeline/
├── api/                        # FastAPI Ingestion Gateway
│   ├── main.py                 # App entrypoint & lifecycle management
│   ├── config.py               # Pydantic BaseSettings
│   ├── routes.py               # /upload, /status, /healthz, /readyz endpoints
│   ├── storage.py              # GCS / MinIO Object storage interface
│   └── kafka_producer.py       # aiokafka event producer
│
├── workers/                    # Background Processing Workers
│   ├── main.py                 # Worker process entrypoint & signal handlers
│   ├── consumer.py             # Kafka consumer loop
│   ├── storage.py              # Raw document fetcher
│   ├── chunker.py              # Semantic text chunking engine
│   ├── embeddings.py           # Local Sentence-Transformers embeddings
│   ├── vector_db.py            # Qdrant client bulk upsert & retries
│   └── dlq.py                  # Dead-Letter Queue error handler
│
├── deploy/                     # Infrastructure & Orchestration
│   ├── docker-compose.yml      # Local dev stack (Zookeeper, Kafka, MinIO, Qdrant, API, Worker)
│   ├── terraform/              # GCP Infrastructure as Code (GKE, GCS, Artifact Registry, IAM)
│   └── helm/                   # Production Helm Chart & KEDA ScaledObject manifest
│
├── scripts/                    # Utilities
│   ├── simulate_load.py        # Bulk document upload load simulator
│   └── setup_graphify.py       # Graphify AST graph launcher
│
├── .graphify/                  # Graphify AST relationship config
├── Dockerfile.api              # Docker image for API Gateway
├── Dockerfile.worker           # Docker image for Worker
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quickstart & Setup Guide

### Option A: Local Execution with Docker Compose

1. **Clone & Environment Setup**:
   ```bash
   cp deploy/.env.example .env
   ```

2. **Spin Up Full Local Stack**:
   ```bash
   docker-compose -f deploy/docker-compose.yml up --build -d
   ```

3. **Verify API Gateway Health**:
   ```bash
   curl http://localhost:8000/v1/readyz
   ```

4. **Run E2E Load Simulation**:
   ```bash
   python scripts/simulate_load.py 15
   ```

---

### Option B: Deploying on Google Cloud Platform (GCP & GKE)

1. **Provision GCP Infrastructure with Terraform**:
   ```bash
   cd deploy/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your GCP project_id
   terraform init
   terraform apply -auto-approve
   ```

2. **Authenticate & Deploy Helm Chart to GKE**:
   ```bash
   gcloud container clusters get-credentials distributed-rag-gke --region us-central1
   helm upgrade --install distributed-rag ./deploy/helm
   ```

---

### Option C: Graphify Knowledge Graph Generation

To generate the code graph visualizer and Leiden community report:
```bash
pip install graphifyy
python scripts/setup_graphify.py
```
View outputs in `graphify-out/` (`GRAPH_REPORT.md`, `graph.html`).

---

## 📄 License
100% Open-Source under the MIT License.
