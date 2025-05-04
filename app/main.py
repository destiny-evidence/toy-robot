"""Main module for the Toy Robot."""

import random
import uuid
from typing import Final

import httpx
from destiny_sdk.core import Annotation, AnnotationEnhancement, EnhancementCreate
from destiny_sdk.robots import RobotError, RobotRequest, RobotResult
from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, status

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


def create_toy_enhancement(request: RobotRequest) -> None:
    """Create a toy annotation enhancement."""
    toy = random.choice(TOYS)  # noqa: S311

    # (TODO) Jack: Enhancement create should include a reference id?
    enhancement = EnhancementCreate(
        source=TITLE,
        visibility="public",
        processor_version="0.1.0",  # replace with project version?
        content_version=f"{uuid.uuid4()}",
        content=AnnotationEnhancement(
            annotations=[
                Annotation(
                    annotation_type="example:toy", label="toy", data={"toy": toy}
                )
            ]
        ),
    )

    robot_result = RobotResult(request_id=request.id, enhancements=[enhancement])

    with httpx.Client() as client:
        client.post(
            request.extra_fields.get("callback_url"),
            json=robot_result.model_dump(mode="json"),
        )


@app.post("/toy/enhancement/", status_code=status.HTTP_202_ACCEPTED)
def request_toy_enhancement(
    request: RobotRequest, background_tasks: BackgroundTasks
) -> Response:
    """Receive a request to create a toy enhancement."""
    if not request.extra_fields.get("callback_url"):
        error = RobotError(
            message="No callback url provided, cannot create enhancement"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    background_tasks.add_task(create_toy_enhancement, request)

    return Response(status_code=status.HTTP_202_ACCEPTED)
