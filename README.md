Distributed RAG Pipeline


  

🚀 Distributed RAG Pipeline

  

    Production-grade, event-driven Retrieval-Augmented Generation (RAG) ingestion platform built for cloud-native AI workloads.
  







Python
FastAPI
Kafka
Kubernetes
Qdrant
License





✨ Overview

Distributed RAG Pipeline is a production-ready ingestion system that decouples document uploads from AI processing using Apache Kafka and Kubernetes event-driven autoscaling.


Features


FastAPI ingestion gateway

Apache Kafka event streaming

Semantic chunking

Sentence Transformers embeddings

Qdrant vector database

MinIO / Google Cloud Storage

Kubernetes + KEDA autoscaling

Dead Letter Queue (DLQ)

Terraform + Helm deployment

Graphify knowledge graph support



🏗 Architecture

flowchart LR

Client([Client])
API[FastAPI Gateway]
Storage[(MinIO / GCS)]
Kafka[(Apache Kafka)]
Workers[KEDA Worker Pool]
Chunk[Semantic Chunking]
Embed[Embedding Model]
Qdrant[(Qdrant)]
DLQ[(Dead Letter Queue)]

Client --> API
API --> Storage
API --> Kafka
Kafka --> Workers
Workers --> Chunk
Chunk --> Embed
Embed --> Qdrant
Workers --> DLQ


📦 Event Flow

sequenceDiagram

participant Client
participant API
participant Storage
participant Kafka
participant Worker
participant Qdrant

Client->>API: Upload document
API->>Storage: Store file
API->>Kafka: Publish event
Kafka->>Worker: Consume
Worker->>Storage: Fetch document
Worker->>Worker: Chunk text
Worker->>Worker: Generate embeddings
Worker->>Qdrant: Upsert vectors


☸ Kubernetes Scaling

flowchart LR

Lag[Kafka Consumer Lag]
KEDA[KEDA]
W1[Worker]
W2[Worker]
WN[Worker N]

Lag --> KEDA
KEDA --> W1
KEDA --> W2
KEDA --> WN


⚙ Tech Stack

Layer	Technology
API	FastAPI
Streaming	Apache Kafka
Storage	MinIO / GCS
Embeddings	Sentence Transformers
Vector DB	Qdrant
Autoscaling	Kubernetes + KEDA
IaC	Terraform
Deployment	Helm
Containerization	Docker


📂 Repository Structure

distributed-rag-pipeline/
├── api/
├── workers/
├── deploy/
│   ├── docker-compose.yml
│   ├── terraform/
│   └── helm/
├── scripts/
├── .graphify/
├── Dockerfile.api
├── Dockerfile.worker
└── README.md


🚀 Quick Start

Local

cp deploy/.env.example .env

docker compose -f deploy/docker-compose.yml up --build -d

curl http://localhost:8000/v1/readyz

python scripts/simulate_load.py 25

Google Kubernetes Engine

cd deploy/terraform

terraform init

terraform apply

gcloud container clusters get-credentials distributed-rag-gke --region us-central1

helm upgrade --install distributed-rag deploy/helm


📈 Why Event Driven?

Traditional synchronous pipelines:


Client
 ↓
API
 ↓
Embedding
 ↓
Database

❌ Slow
❌ Blocking
❌ Difficult to scale

Distributed architecture:


Client
 ↓
FastAPI
 ↓
Kafka
 ↓
Worker Pool
 ↓
Qdrant

✅ Fault tolerant
✅ Horizontally scalable
✅ High throughput


🔄 Failure Recovery

flowchart LR

Worker --> Retry
Retry --> Success
Retry --> DLQ


📊 Production Highlights


Stateless workers

Horizontal autoscaling

Event-driven processing

Retry with exponential backoff

Dead Letter Queue

Infrastructure as Code

Cloud-native deployment

Open-source stack



🛣 Roadmap


OCR pipeline

Hybrid search

Reranking

Multimodal ingestion

Streaming embeddings

Monitoring dashboards

CI/CD improvements



📄 License

Released under the MIT License.

