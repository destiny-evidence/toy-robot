"""Main module for the Toy Robot."""

import asyncio
import contextlib
import logging
import signal
import sys
from types import FrameType
from typing import Final

import destiny_sdk

from app.config import configure_logging, get_settings
from app.enhancement_processor import ToyEnhancementProcessor

# Configure logging for the application
configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

TITLE: Final[str] = "Toy Robot"

client = destiny_sdk.client.Client(
    base_url=settings.destiny_repository_url,
    client_id=settings.robot_id,
    secret_key=settings.robot_secret,
)

processor = ToyEnhancementProcessor(
    robot_version=settings.robot_version,
    source_name=TITLE,
)


async def process_robot_enhancement_batch(
    batch: destiny_sdk.robots.RobotEnhancementBatch,
) -> None:
    """Process a single robot enhancement batch by creating toy enhancements."""
    try:
        await processor.process_batch(batch)

        client.send_robot_enhancement_batch_result(
            destiny_sdk.robots.RobotEnhancementBatchResult(request_id=batch.id)
        )

        logger.info("Successfully processed robot enhancement batch %s", batch.id)

    except Exception as e:
        logger.exception("Error processing robot enhancement batch %s", batch.id)

        client.send_robot_enhancement_batch_result(
            destiny_sdk.robots.RobotEnhancementBatchResult(
                request_id=batch.id,
                error=destiny_sdk.robots.RobotError(
                    message=f"Failed to process request: {e!s}"
                ),
            )
        )
        raise


async def poll_for_batches() -> None:
    """Poll for new robot enhancement batches and process them."""
    logger.info("Starting to poll for robot enhancement batches...")

    while True:
        try:
            batch = client.poll_robot_enhancement_batch(
                robot_id=settings.robot_id, limit=settings.batch_size
            )

            if batch is None:
                logger.debug("No batches available")
                await asyncio.sleep(settings.poll_interval_seconds)
                continue

            logger.info("Found batch %s to process", batch.id)

            try:
                await process_robot_enhancement_batch(batch)
            except Exception:
                logger.exception("Error processing batch %s", batch.id)

        except Exception:
            logger.exception("Error during polling")

        await asyncio.sleep(settings.poll_interval_seconds)


shutdown_event = asyncio.Event()


def signal_handler(signum: int, _frame: FrameType | None) -> None:
    """Handle shutdown signals gracefully."""
    logger.info("Received signal %s, initiating graceful shutdown...", signum)
    shutdown_event.set()


async def main() -> None:
    """Run the polling robot."""
    logger.info("Starting %s polling loop", TITLE)
    logger.info("Polling interval: %d seconds", settings.poll_interval_seconds)
    logger.info("Batch size: %d", settings.batch_size)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        poll_task = asyncio.create_task(poll_for_batches())

        # Wait for either the polling task to complete or shutdown signal
        done, pending = await asyncio.wait(
            [poll_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        logger.info("Shutdown complete")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        sys.exit(0)
    except Exception:
        logger.exception("Fatal error occurred")
        sys.exit(1)
