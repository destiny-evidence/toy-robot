"""Test the main module."""

import uuid

import destiny_sdk
from fastapi import status
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock, IteratorStream

from app.main import app

client = TestClient(app)


def test_root() -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "I am a Toy Robot"}


def test_create_toy_enhancements_happy_path(httpx_mock: HTTPXMock) -> None:
    """Test that we can create toy enhancements."""
    request_id = uuid.uuid4()
    reference_ids = [uuid.uuid4() for _ in range(3)]

    mock_reference_file_stream(httpx_mock, reference_ids)
    mock_destiny_repository_response(httpx_mock, request_id, reference_ids)
    mock_enhancement_put(httpx_mock)

    request_body = destiny_sdk.robots.RobotRequest(
        id=uuid.uuid4(),
        reference_storage_url="https://get-references-here.com",
        result_storage_url="https://get-enhancements-here.com",
    ).model_dump(mode="json")

    response = client.post("/toy/enhancement/batch/", json=request_body)

    assert response.status_code == status.HTTP_202_ACCEPTED

    # Assert the background task has been called.
    callback_requests = httpx_mock.get_requests()
    assert len(callback_requests) == 3

    # Assert that we put three enhancements in the results storage
    put_request = callback_requests[1]
    generated_enhancements = put_request.content.decode("utf-8").strip().split("\n")
    assert len(generated_enhancements) == 3

    # Assert the enhancements are valid
    for enhancement in generated_enhancements:
        destiny_sdk.enhancements.Enhancement.from_jsonl(enhancement)


def mock_reference_file_stream(httpx_mock: HTTPXMock, reference_ids: list[uuid.UUID]):
    """Mock a stream for a file containing references."""
    stream_response = []
    for reference_id in reference_ids:
        reference = destiny_sdk.references.Reference(
            id=reference_id,
        )
        stream_response.append(bytes(reference.to_jsonl() + "\n", "utf-8"))
    httpx_mock.add_response(stream=IteratorStream(stream_response))


def mock_destiny_repository_response(
    httpx_mock: HTTPXMock, request_id: uuid.UUID, reference_ids: list[uuid.UUID]
):
    """Mock a successful enhancement post to destiny repository."""
    create_enhancement_response = destiny_sdk.robots.EnhancementRequestRead(
        id=request_id,
        reference_ids=reference_ids,
        enhancement_parameters={},
        robot_id=uuid.uuid4(),
        request_status=destiny_sdk.robots.EnhancementRequestStatus.COMPLETED,
    )

    # Mock out our callback
    httpx_mock.add_response(
        method="POST",
        status_code=status.HTTP_200_OK,
        json=create_enhancement_response.model_dump(mode="json"),
    )


def mock_enhancement_put(httpx_mock: HTTPXMock):
    """Mock the putting of references to the results url."""
    httpx_mock.add_response(method="PUT", status_code=status.HTTP_200_OK)
