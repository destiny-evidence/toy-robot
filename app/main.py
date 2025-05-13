"""Main module for the Toy Robot."""

import random
import uuid
from typing import Final

import destiny_sdk
import httpx
import msal
from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, status

from app.config import get_settings

settings = get_settings()

TITLE: Final[str] = "Toy Robot"
app = FastAPI(title=TITLE)


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint for the API.

    Returns:
        dict[str, str]: A simple message.

    """
    return {"message": "I am a Toy Robot"}


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
]


def build_toy_enhancement(
    request: destiny_sdk.robots.RobotRequest,
) -> destiny_sdk.robots.RobotResult:
    """Build the request body for creating an enhancement."""
    toy = random.choice(TOYS)  # noqa: S311

    enhancement = destiny_sdk.enhancements.Enhancement(
        reference_id=request.reference.id,
        source=TITLE,
        visibility=request.reference.visibility,
        robot_version="0.1.0",
        content_version=f"{uuid.uuid4()}",
        content=destiny_sdk.enhancements.AnnotationEnhancement(
            annotations=[
                destiny_sdk.enhancements.Annotation(
                    annotation_type="example:toy", label="toy", data={"toy": toy}
                )
            ]
        ),
    )

    return destiny_sdk.robots.RobotResult(
        request_id=request.id, enhancement=enhancement
    )


def create_toy_enhancement(request: destiny_sdk.robots.RobotRequest) -> None:
    """Send request to creat an toy enhancement."""
    robot_result = build_toy_enhancement(request)

    if settings.env != "dev":
        auth_client = msal.ManagedIdentityClient(
            managed_identity=msal.UserAssignedManagedIdentity(
                client_id=settings.azure_client_id
            ),
            http_client=httpx.Client(),
        )

        auth_client.acquire_token_for_client(resource=settings.azure_application_url)

    with httpx.Client() as client:
        client.post(
            request.extra_fields.get("callback_url"),
            json=robot_result.model_dump(mode="json"),
        )


@app.post("/toy/enhancement/", status_code=status.HTTP_202_ACCEPTED)
def request_toy_enhancement(
    request: destiny_sdk.robots.RobotRequest, background_tasks: BackgroundTasks
) -> Response:
    """Receive a request to create a toy enhancement."""
    if not request.extra_fields.get("callback_url"):
        error = destiny_sdk.robots.RobotError(
            message="No callback url provided, cannot create enhancement"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    background_tasks.add_task(create_toy_enhancement, request)

    return Response(status_code=status.HTTP_202_ACCEPTED)
