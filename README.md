# Distributed RAG Pipeline (`distributed-rag-pipeline`)

A production-grade, 100% open-source, event-driven Retrieval-Augmented Generation (RAG) ingestion pipeline engineered for sub-second document indexing, high-throughput event processing, and cloud-native Kubernetes scaling.

Built with **FastAPI**, **Apache Kafka**, **MinIO / Google Cloud Storage (GCS)**, **Qdrant Vector Engine**, **Hugging Face Sentence-Transformers**, **KEDA (Kubernetes Event-driven Autoscaling)**, and **Graphify** knowledge graph codebase mapping.

---

## 🏗️ System Architecture & Event Flow

```text
                 +-------------------------------------------------------------+
                 |                         CLIENT / SINK                       |
                 +-------------------------------------------------------------+
                                        |
                                 POST /v1/documents/upload
                                        v
                            +------------------+
                            | FastAPI Gateway  |
                            |      (api/)      |
                            +------------------+
                              /              \
               1. Stream Raw Bytes           2. Publish Upload Event
                            /                  \
                           v                    v
                +-----------------------+    +-------------------+
                | Object Storage Layer  |    |    Apache Kafka   |
                |  (GCP GCS / MinIO)    |    | Topic: document-  |
                +-----------------------+    |     uploaded      |
                         ^                   +-------------------+
                         |                             |
                 Fetch Document Text                   | Consumer Lag
                         |                             v
                +----------------------------------------------------------------+
                |                KEDA Worker Pod Pool (workers/)                 |
                |             [Scaled 1 -> N pods based on Kafka Lag]            |
                +----------------------------------------------------------------+
                   /                    |                \              \
            Semantic Chunking  Embedding Generation    Qdrant Bulk   On Failure
           (workers/chunker.py)(Sentence-Transformers)  Upserting       (DLQ)
                   \                    |                /              /
                    v                    v                v              v
                +--------------------------------+    +------------------+
                |   Qdrant Vector Database       |    |   Apache Kafka   |
                |   (Collection: rag_documents)  |    | Topic: doc-dlq   |
                +--------------------------------+    +------------------+
⚡ Core Operational Deep-Dives
1. Event-Driven Scaling with KEDA
Mechanics: KEDA polls Apache Kafka consumer group lag on the document-uploaded topic every 15 seconds via the ScaledObject controller (deploy/helm/templates/scaledobject.yaml).

Behavior: When lag exceeds 10 messages per group, KEDA dynamically scales worker pods on Google Kubernetes Engine (GKE) up to a maximum of 10 replicas. Once consumer lag clears, it scales worker pods down to zero to optimize infrastructure costs.

2. Dead-Letter Queue (DLQ) Error Isolation
Resilience: Transient storage or vector DB failures invoke automatic exponential backoff retries via the tenacity decorator inside vector_db.py.

Isolation: Unrecoverable failures (e.g., corrupted file formatting, invalid JSON payloads, or exhausted retry limits) are captured by workers/dlq.py and routed safely to the document-dlq Kafka topic with comprehensive metadata, preventing worker pool crashes.

3. Dual Object Storage Abstraction
Flexibility: Features a unified storage abstraction layer (api/storage.py & workers/storage.py) that seamlessly switches between local S3-compatible MinIO for local development and native Google Cloud Storage (GCS) for production environments via GCP Workload Identity.

4. Graphify AST Knowledge Graph Navigation
Code Mapping: Leverages tree-sitter AST parsing and Leiden community clustering (configured in .graphify/config.json) to generate deterministic code structure maps (graphify-out/). This empowers AI coding agents to traverse function boundaries, class hierarchies, and dependencies without brute-force grep or token waste.

📂 Repository Structure
Plaintext
distributed-rag-pipeline/
├── api/                       # FastAPI Ingestion Gateway
│   ├── main.py                # App entrypoint & lifecycle management
│   ├── config.py              # Pydantic BaseSettings
│   ├── routes.py              # /upload, /status, /healthz, /readyz endpoints
│   ├── storage.py             # GCS / MinIO Object storage interface
│   └── kafka_producer.py      # aiokafka event producer
│
├── workers/                   # Background Processing Workers
│   ├── main.py                # Worker process entrypoint & signal handlers
│   ├── consumer.py            # Kafka consumer loop
│   ├── storage.py             # Raw document fetcher
│   ├── chunker.py             # Semantic text chunking engine
│   ├── embeddings.py          # Local Sentence-Transformers embeddings
│   ├── vector_db.py           # Qdrant client bulk upsert & retries
│   └── dlq.py                 # Dead-Letter Queue error handler
│
├── deploy/                    # Infrastructure & Orchestration
│   ├── docker-compose.yml     # Local dev stack (Zookeeper, Kafka, MinIO, Qdrant, API, Worker)
│   ├── terraform/             # GCP Infrastructure as Code (GKE, GCS, Artifact Registry, IAM)
│   └── helm/                  # Production Helm Chart & KEDA ScaledObject manifest
│
├── scripts/                   # Utilities
│   ├── simulate_load.py       # Bulk document upload load simulator
│   └── setup_graphify.py      # Graphify AST graph launcher
│
├── .graphify/                 # Graphify AST relationship config
├── Dockerfile.api             # Docker image for API Gateway
├── Dockerfile.worker          # Docker image for Worker
└── requirements.txt           # Python dependencies
🚀 Quickstart & Setup Guide
Option A: Local Execution with Docker Compose
Clone and Configure Environment:

Bash
cp deploy/.env.example .env
Spin Up the Local Stack:

Bash
docker-compose -f deploy/docker-compose.yml up --build -d
Verify API Gateway Health:

Bash
curl http://localhost:8000/v1/readyz
Run End-to-End Load Simulation:

Bash
python scripts/simulate_load.py 15
Option B: Deploying on Google Cloud Platform (GCP & GKE)
Provision Infrastructure with Terraform:

Bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project_id and configurations
terraform init
terraform apply -auto-approve
Authenticate and Deploy Helm Chart to GKE:

Bash
gcloud container clusters get-credentials distributed-rag-gke --region us-central1
helm upgrade --install distributed-rag ./deploy/helm
Option C: Graphify Knowledge Graph Generation
To generate code graph visualizers and community layout reports:

Bash
pip install graphifyy
python scripts/setup_graphify.py
Outputs are saved to graphify-out/ (GRAPH_REPORT.md, graph.html).

📄 License
100% Open-Source under the MIT License.
