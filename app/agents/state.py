from __future__ import annotations

from datetime import date
from typing import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

from app.schemas.availability import AvailabilityResponse
from app.schemas.booking import BookingResponse


class BookingState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]

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
    booking_confirmed: bool

    # Validation
    requirements_error: str | None