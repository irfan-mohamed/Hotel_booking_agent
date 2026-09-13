from datetime import date

from app.schemas.availability import (
    AvailabilityRequest,
    AvailabilityResponse,
)
from app.services.availability_service import AvailabilityService


class AvailabilityTool:
    """
    Tool boundary between the conversational agent
    and the availability business service.

    The tool is intentionally thin:
        Agent
            ↓
        AvailabilityTool
            ↓
        AvailabilityService
            ↓
        RoomRepository
            ↓
        PostgreSQL
    """

    def __init__(
        self,
        availability_service: AvailabilityService,
    ):
        self.availability_service = availability_service

    def check_room_availability(
        self,
        check_in: date,
        check_out: date,
        bed_type: str,
        breakfast: bool,
        guests: int,
    ) -> AvailabilityResponse:
        """
        Check room availability for the requested stay.

        Args:
            check_in:
                Guest check-in date.

            check_out:
                Guest check-out date.

            bed_type:
                Requested bed type: "single" or "double".

            breakfast:
                Whether breakfast is required.

            guests:
                Number of guests staying.

        Returns:
            AvailabilityResponse containing one of:

            - exact_match
            - alternatives
            - fully_booked

        Raises:
            ValueError:
                If the request contains invalid dates,
                an invalid guest count, or a past check-in date.
        """

        request = AvailabilityRequest(
            check_in=check_in,
            check_out=check_out,
            bed_type=bed_type,
            breakfast=breakfast,
            guests=guests,
        )

        return self.availability_service.check_availability(
            request
        )


def check_room_availability(
    availability_service: AvailabilityService,
    check_in: date,
    check_out: date,
    bed_type: str,
    breakfast: bool,
    guests: int,
) -> AvailabilityResponse:
    """
    Function-style wrapper around AvailabilityTool.

    This function is useful when exposing the capability
    to an LLM framework that expects callable tools.
    """

    tool = AvailabilityTool(
        availability_service=availability_service,
    )

    return tool.check_room_availability(
        check_in=check_in,
        check_out=check_out,
        bed_type=bed_type,
        breakfast=breakfast,
        guests=guests,
    )

