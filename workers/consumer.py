import json
import logging
import asyncio
from typing import Optional
from aiokafka import AIOKafkaConsumer
from workers.config import settings
from workers.storage import worker_storage
from workers.chunker import chunker_engine
from workers.embeddings import embedding_pipeline
from workers.vector_db import qdrant_store
from workers.dlq import dlq_handler

logger = logging.getLogger(__name__)


class DocumentProcessingConsumer:
    """Async Kafka consumer consuming document events and orchestrating pipeline stages."""

    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.is_running = False

    async def start(self):
        """Starts Kafka consumer connection and joins consumer group."""
        self.consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_DOCUMENT_UPLOADED,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self.consumer.start()
        await dlq_handler.start()
        self.is_running = True
        logger.info(
            "Consumer connected to Kafka bootstrap servers %s [Topic: %s, Group: %s]",
            settings.KAFKA_BOOTSTRAP_SERVERS,
            settings.KAFKA_TOPIC_DOCUMENT_UPLOADED,
            settings.KAFKA_CONSUMER_GROUP_ID,
        )

    async def stop(self):
        """Gracefully stops consumer and flushes commits."""
        self.is_running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("AIOKafkaConsumer stopped.")
        await dlq_handler.stop()

    async def process_event(self, event_data: dict):
        """Processes single document upload event end-to-end."""
        doc_id = event_data.get("document_id")
        filename = event_data.get("filename")
        bucket_name = event_data.get("bucket_name")
        object_key = event_data.get("object_key")

        logger.info("Processing ingestion event for doc_id: %s [file: %s]", doc_id, filename)

        # Stage 1: Fetch raw document text from Object Storage (GCS / MinIO)
        try:
            raw_text = worker_storage.fetch_document_text(bucket_name, object_key)
        except Exception as e:
            logger.error("Failed to fetch document text for doc_id: %s", doc_id)
            await dlq_handler.send_to_dlq(event_data, e, context="STORAGE_FETCH_FAILURE")
            return

        # Stage 2: Semantic text chunking
        try:
            chunks = chunker_engine.chunk_text(raw_text, doc_id, filename)
            if not chunks:
                logger.warning("No text chunks generated for doc_id: %s", doc_id)
                return
        except Exception as e:
            logger.error("Failed to chunk document text for doc_id: %s", doc_id)
            await dlq_handler.send_to_dlq(event_data, e, context="TEXT_CHUNKING_FAILURE")
            return

        # Stage 3: Embedding generation
        try:
            texts = [c["text"] for c in chunks]
            vectors = embedding_pipeline.generate_embeddings(texts)
        except Exception as e:
            logger.error("Failed to generate embeddings for doc_id: %s", doc_id)
            await dlq_handler.send_to_dlq(event_data, e, context="EMBEDDING_GENERATION_FAILURE")
            return

        # Stage 4: Qdrant Bulk Upsert with Retries
        try:
            qdrant_store.upsert_chunks(chunks, vectors)
            logger.info("Successfully completed ingestion pipeline for doc_id: %s (%d chunks)", doc_id, len(chunks))
        except Exception as e:
            logger.error("Exhausted retries upserting vectors to Qdrant for doc_id: %s", doc_id)
            await dlq_handler.send_to_dlq(event_data, e, context="VECTOR_DB_UPSERT_FAILURE")

    async def run_loop(self):
        """Main event consumption loop with explicit offset commits."""
        await self.start()
        try:
            while self.is_running:
                result = await self.consumer.getmany(timeout_ms=1000, max_records=10)
                for tp, messages in result.items():
                    for msg in messages:
                        try:
                            await self.process_event(msg.value)
                            await self.consumer.commit({tp: msg.offset + 1})
                        except Exception as unhandled_err:
                            logger.error("Unhandled exception processing record offset %d: %s", msg.offset, str(unhandled_err))
                            await dlq_handler.send_to_dlq(msg.value, unhandled_err, context="UNHANDLED_CONSUMER_LOOP_ERROR")
                            await self.consumer.commit({tp: msg.offset + 1})
        except asyncio.CancelledError:
            logger.info("Consumer run loop cancelled.")
        finally:
            await self.stop()
