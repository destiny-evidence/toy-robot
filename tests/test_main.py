"""Test the main module."""

import uuid

from fastapi import status
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

from app.main import app

client = TestClient(app)


def test_root() -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "I am a Toy Robot"}


def test_create_toy_enhancement_happy_path(httpx_mock: HTTPXMock) -> None:
    """Test that we can create an enhancement."""
    request_id = uuid.uuid4()

    # Mock out our callback
    httpx_mock.add_response(method="POST", status_code=status.HTTP_201_CREATED)

    request_body = {
        "id": f"{request_id}",
        "reference": {"id": f"{uuid.uuid4()}", "identifiers": [], "enhancements": []},
        "extra_fields": {},
    }

    response = client.post("/toy/enhancement", json=request_body)

    assert response.status_code == status.HTTP_202_ACCEPTED

    # Assert the background task has been called.
    callback_request = httpx_mock.get_requests()
    assert len(callback_request) == 1
