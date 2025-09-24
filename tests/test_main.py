"""Test the main module."""

import os
import uuid
from unittest.mock import patch

import destiny_sdk
import httpx
import pytest
from pytest_httpx import HTTPXMock, IteratorStream

# Set required environment variables for testing
os.environ.setdefault("ROBOT_SECRET", "test_secret")
os.environ.setdefault("ROBOT_ID", str(uuid.uuid4()))
os.environ.setdefault("DESTINY_REPOSITORY_URL", "https://test.example.com")

from app.main import TOYS, generate_toy_enhancement, process_robot_enhancement_batch


def test_generate_toy_enhancement() -> None:
    """Test that toy enhancements are generated with valid toy names."""
    reference_id = uuid.uuid4()

    enhancement = generate_toy_enhancement(reference_id)

    assert enhancement.reference_id == reference_id
    assert isinstance(
        enhancement.content, destiny_sdk.enhancements.AnnotationEnhancement
    )
    assert len(enhancement.content.annotations) > 0
    annotation = enhancement.content.annotations[0]
    assert isinstance(annotation, destiny_sdk.enhancements.ScoreAnnotation)
    assert annotation.data["toy"] in TOYS


@pytest.mark.asyncio
async def test_process_robot_enhancement_batch_happy_path(
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful processing of a robot enhancement batch."""
    batch_id = uuid.uuid4()
    reference_ids = [uuid.uuid4() for _ in range(3)]

    # Mock the batch data
    batch = destiny_sdk.robots.RobotEnhancementBatch(
        id=batch_id,
        reference_storage_url="https://get-references-here.com",
        result_storage_url="https://put-results-here.com",
    )

    # Mock reference file download
    mock_reference_file_stream(httpx_mock, reference_ids)

    # Mock result upload
    httpx_mock.add_response(method="PUT", status_code=200)

    # Mock SDK result submission
    with patch("app.main.client") as mock_client:
        # Process the batch
        await process_robot_enhancement_batch(batch)

        # Verify SDK was called with success result
        mock_client.send_robot_enhancement_batch_result.assert_called_once()
        call_args = mock_client.send_robot_enhancement_batch_result.call_args[0][0]
        assert call_args.request_id == batch_id
        assert call_args.error is None


@pytest.mark.asyncio
async def test_process_robot_enhancement_batch_with_download_error(
    httpx_mock: HTTPXMock,
) -> None:
    """Test handling of download errors during batch processing."""
    batch_id = uuid.uuid4()

    batch = destiny_sdk.robots.RobotEnhancementBatch(
        id=batch_id,
        reference_storage_url="https://get-references-here.com",
        result_storage_url="https://put-results-here.com",
    )

    # Mock download failure
    httpx_mock.add_response(method="GET", status_code=404)

    with patch("app.main.client") as mock_client:
        # Process should raise an exception due to HTTP error
        with pytest.raises(httpx.HTTPStatusError, match="404"):
            await process_robot_enhancement_batch(batch)

        # Verify error result was sent
        mock_client.send_robot_enhancement_batch_result.assert_called_once()
        call_args = mock_client.send_robot_enhancement_batch_result.call_args[0][0]
        assert call_args.request_id == batch_id
        assert call_args.error is not None


def mock_reference_file_stream(httpx_mock: HTTPXMock, reference_ids: list[uuid.UUID]):
    """Mock a stream for a file containing references."""
    stream_response = []
    for reference_id in reference_ids:
        reference = destiny_sdk.references.Reference(
            id=reference_id,
        )
        stream_response.append(bytes(reference.to_jsonl() + "\n", "utf-8"))
    httpx_mock.add_response(stream=IteratorStream(stream_response))
