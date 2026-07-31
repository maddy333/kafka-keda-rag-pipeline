import json
import logging
from typing import Optional
from aiokafka import AIOKafkaProducer
from api.config import settings
from api.schemas import DocumentEventMessage

logger = logging.getLogger(__name__)


class AsyncKafkaProducerWrapper:
    """Async Kafka Producer managing event publishing to document-uploaded topic."""

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        """Starts the aiokafka producer connection."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=5,
            )
            await self.producer.start()
            logger.info("AIOKafkaProducer started successfully on %s", settings.KAFKA_BOOTSTRAP_SERVERS)
        except Exception as e:
            logger.error("Failed to start AIOKafkaProducer: %s", str(e))
            self.producer = None

    async def stop(self):
        """Gracefully stops the producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("AIOKafkaProducer stopped.")

    async def send_document_event(self, event: DocumentEventMessage) -> bool:
        """Publishes document ingestion event message to Kafka."""
        if not self.producer:
            logger.error("Kafka producer is not connected.")
            return False

        try:
            record_metadata = await self.producer.send_and_wait(
                topic=settings.KAFKA_TOPIC_DOCUMENT_UPLOADED,
                key=event.document_id,
                value=event.model_dump(),
            )
            logger.info(
                "Event sent to topic %s [partition %d, offset %d] for doc_id: %s",
                record_metadata.topic,
                record_metadata.partition,
                record_metadata.offset,
                event.document_id,
            )
            return True
        except Exception as e:
            logger.error("Failed to publish document event for %s: %s", event.document_id, str(e))
            return False

    async def check_health(self) -> bool:
        """Health check probe verifying producer status."""
        return self.producer is not None


kafka_producer = AsyncKafkaProducerWrapper()
