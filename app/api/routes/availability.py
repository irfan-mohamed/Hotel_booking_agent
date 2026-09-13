from fastapi import APIRouter, Depends

from app.api.dependencies import get_availability_tool
from app.schemas.availability import (
    AvailabilityRequest,
    AvailabilityResponse,
)
from app.tools.availability_tool import AvailabilityTool


router = APIRouter(
    prefix="/availability",
    tags=["Availability"],
)


@router.post(
    "",
    response_model=AvailabilityResponse,
)
def check_availability(
    request: AvailabilityRequest,
    tool: AvailabilityTool = Depends(get_availability_tool),
) -> AvailabilityResponse:
    """
    Check room availability for the requested dates
    and preferences.
    """

    return tool.check_availability(
        request=request,
    )