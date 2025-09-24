"""Main module for the Toy Robot."""

import asyncio
import contextlib
import logging
import random
import signal
import sys
import uuid
from types import FrameType
from typing import Final
from uuid import UUID

import destiny_sdk
import httpx

from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

TITLE: Final[str] = "Toy Robot"

client = destiny_sdk.client.Client(
    base_url=settings.destiny_repository_url,
    client_id=settings.robot_id,
    secret_key=settings.robot_secret,
)

TOYS = [
    "Woody",
    "Jessie",
    "Bullseye",
    "Stinky Pete",
    "Buzz Lightyear",
    "Rex",
    "Mr. Potatohead",
    "Mrs. Potato Head",
    "Bo Peep",
    "Slinky Dog",
    "Etch a Sketch",
    "Hamm",
    "Lenny",
    "Emperor Zurg",  # uh oh
    # proof by induction
    "Little Green Man 1",
    "Little Green Man n",
    "Little Green Man n+1",
]


def generate_toy_enhancement(
    reference_id: UUID,
) -> destiny_sdk.enhancements.Enhancement:
    """Generate a toy enhancement."""
    return destiny_sdk.enhancements.Enhancement(
        reference_id=reference_id,
        source=TITLE,
        visibility=destiny_sdk.visibility.Visibility.PUBLIC,
        robot_version=settings.robot_version,
        content_version=f"{uuid.uuid4()}",
        content=destiny_sdk.enhancements.AnnotationEnhancement(
            annotations=[
                destiny_sdk.enhancements.ScoreAnnotation(
                    annotation_type="score",
                    label="toy",
                    scheme="meta:toy",
                    data={"toy": random.choice(TOYS)},  # noqa: S311
                    score=round(random.randint(0, 100) / 100, 2),  # noqa: S311
                )
            ]
        ),
    )


async def process_robot_enhancement_batch(
    batch: destiny_sdk.robots.RobotEnhancementBatch,
) -> None:
    """Process a single robot enhancement batch by creating toy enhancements."""
    logger.info("Processing robot enhancement batch %s", batch.id)

    try:
        file_content = b""
        async with (
            httpx.AsyncClient() as httpx_client,
            httpx_client.stream("GET", str(batch.reference_storage_url)) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                reference = destiny_sdk.references.Reference.model_validate_json(line)
                enhancement = generate_toy_enhancement(reference.id)
                file_content += (enhancement.to_jsonl() + "\n").encode("utf-8")

        # Upload the results
        async with httpx.AsyncClient() as httpx_client:
            response = await httpx_client.put(
                str(batch.result_storage_url),
                content=file_content,
                headers={
                    "Content-Type": "application/jsonl",
                    "x-ms-blob-type": "BlockBlob",
                    "Content-Length": str(len(file_content)),
                },
            )
            response.raise_for_status()

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
