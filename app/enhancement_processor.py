"""Enhancement processing logic for the Toy Robot."""

import logging
import random
import uuid
from typing import Final
from uuid import UUID

import destiny_sdk
import httpx

logger = logging.getLogger(__name__)

TOYS: Final[list[str]] = [
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


class ToyEnhancementProcessor:
    """Handles the processing of robot enhancement batches."""

    def __init__(self, robot_version: str, source_name: str = "Toy Robot") -> None:
        """Initialize the processor with configuration."""
        self.robot_version = robot_version
        self.source_name = source_name

    def generate_toy_enhancement(
        self, reference_id: UUID
    ) -> destiny_sdk.enhancements.Enhancement:
        """Generate a toy enhancement for a reference."""
        return destiny_sdk.enhancements.Enhancement(
            reference_id=reference_id,
            source=self.source_name,
            visibility=destiny_sdk.visibility.Visibility.PUBLIC,
            robot_version=self.robot_version,
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

    async def download_references(
        self, reference_storage_url: str
    ) -> list[destiny_sdk.references.Reference]:
        """Download and parse references from storage URL."""
        references = []
        async with (
            httpx.AsyncClient() as client,
            client.stream("GET", reference_storage_url) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                reference = destiny_sdk.references.Reference.model_validate_json(
                    line
                )
                references.append(reference)
        return references

    async def upload_enhancements(
        self,
        enhancements: list[destiny_sdk.enhancements.Enhancement],
        result_storage_url: str,
    ) -> None:
        """Upload enhancements to storage URL."""
        file_content = b""
        for enhancement in enhancements:
            file_content += (enhancement.to_jsonl() + "\n").encode("utf-8")

        async with httpx.AsyncClient() as client:
            response = await client.put(
                result_storage_url,
                content=file_content,
                headers={
                    "Content-Type": "application/jsonl",
                    "x-ms-blob-type": "BlockBlob",
                    "Content-Length": str(len(file_content)),
                },
            )
            response.raise_for_status()

    async def process_batch(
        self, batch: destiny_sdk.robots.RobotEnhancementBatch
    ) -> list[destiny_sdk.enhancements.Enhancement]:
        """Process a batch by downloading references and creating enhancements."""
        logger.info("Processing robot enhancement batch %s", batch.id)

        references = await self.download_references(str(batch.reference_storage_url))
        enhancements = [self.generate_toy_enhancement(ref.id) for ref in references]
        await self.upload_enhancements(enhancements, str(batch.result_storage_url))

        return enhancements
