import signal
import asyncio
import logging
from workers.config import settings
from workers.consumer import DocumentProcessingConsumer

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting Distributed RAG Worker: %s", settings.WORKER_NAME)
    consumer = DocumentProcessingConsumer()

    loop = asyncio.get_running_loop()

    def shutdown_signal_handler():
        logger.info("Received termination signal. Triggering consumer shutdown...")
        asyncio.create_task(consumer.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_signal_handler)
        except NotImplementedError:
            # Signal handling on Windows event loop fallback
            pass

    try:
        await consumer.run_loop()
    except Exception as e:
        logger.critical("Worker crashed with error: %s", str(e))
    finally:
        logger.info("Worker process terminated cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
