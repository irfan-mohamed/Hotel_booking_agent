from fastapi import APIRouter, Depends

from app.api.dependencies import get_booking_tool
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
)
from app.tools.booking_tool import BookingTool


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


@router.post(
    "",
    response_model=BookingResponse,
)
def create_booking(
    request: BookingCreate,
    tool: BookingTool = Depends(get_booking_tool),
) -> BookingResponse:
    """
    Create a hotel booking.
    """

    return tool.create_booking(
        request=request,
    )