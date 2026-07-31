import json
import logging
from datetime import datetime
from typing import Dict, Any
from aiokafka import AIOKafkaProducer
from workers.config import settings

logger = logging.getLogger(__name__)


class DeadLetterQueueHandler:
    """Dead-Letter Queue handler isolating unrecoverable processing failures into Kafka DLQ topic."""

    def __init__(self):
        self.producer = None

    async def start(self):
        """Starts Kafka producer for DLQ topic."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await self.producer.start()
            logger.info("DLQ Producer started on %s", settings.KAFKA_BOOTSTRAP_SERVERS)
        except Exception as e:
            logger.error("Failed to start DLQ Producer: %s", str(e))

    async def stop(self):
        """Stops DLQ producer."""
        if self.producer:
            await self.producer.stop()

    async def send_to_dlq(self, original_event: Dict[str, Any], error: Exception, context: str):
        """Publishes failed event payload with exception context to DLQ topic."""
        dlq_payload = {
            "original_event": original_event,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "failure_context": context,
            "failed_at": datetime.utcnow().isoformat(),
            "worker_name": settings.WORKER_NAME,
        }

        doc_id = original_event.get("document_id", "unknown")
        logger.error(
            "Routing unrecoverable failure for doc_id: %s to DLQ topic '%s'. Error: %s",
            doc_id,
            settings.KAFKA_TOPIC_DLQ,
            str(error),
        )

        if self.producer:
            try:
                await self.producer.send_and_wait(
                    topic=settings.KAFKA_TOPIC_DLQ,
                    key=doc_id,
                    value=dlq_payload,
                )
                logger.info("Successfully pushed payload for doc_id: %s to DLQ topic", doc_id)
            except Exception as dlq_err:
                logger.critical("Failed to send message to DLQ topic: %s", str(dlq_err))


dlq_handler = DeadLetterQueueHandler()
