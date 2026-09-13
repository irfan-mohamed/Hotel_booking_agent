from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.messages import BaseMessage

from app.schemas.availability import AvailabilityResponse
from app.schemas.booking import BookingResponse


class BookingState(TypedDict, total=False):

    messages: list[BaseMessage]

    # Search requirements
    check_in: date | None
    check_out: date | None
    bed_type: str | None
    breakfast: bool | None
    guests: int | None

    # Availability
    availability: AvailabilityResponse | None
    availability_checked: bool

    # Selection
    selected_room_id: int | None
    selected_room_no: int | None

    # Guest
    guest_name: str | None
    guest_email: str | None

    # Booking
    booking: BookingResponse | None
    booking_error: str | None

    # Validation
    requirements_error: str | None