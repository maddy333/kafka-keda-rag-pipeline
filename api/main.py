import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.routes import router
from api.kafka_producer import kafka_producer

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing Kafka producer lifecycle."""
    logger.info("Starting up FastAPI application '%s'...", settings.PROJECT_NAME)
    await kafka_producer.start()
    yield
    logger.info("Shutting down FastAPI application...")
    await kafka_producer.stop()


app = FastAPI(
    title="Distributed RAG Ingestion API Gateway",
    description="FastAPI service for document uploads, GCS/MinIO storage, and Kafka event streaming.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Distributed RAG Pipeline API Gateway",
        "docs": "/docs",
        "health": "/v1/healthz",
    }
