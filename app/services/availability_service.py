from datetime import date

from app.repositories.room_repository import RoomRepository
from app.schemas.availability import (
    AvailabilityRequest,
    AvailabilityResponse,
    RoomAvailability,
)
from app.services.alternative_service import AlternativeService


class AvailabilityService:
    """
    Business logic for checking hotel room availability.
    """

    def __init__(
        self,
        room_repository: RoomRepository,
        alternative_service: AlternativeService,
    ):
        self.room_repository = room_repository
        self.alternative_service = alternative_service

    def check_availability(
        self,
        request: AvailabilityRequest,
    ) -> AvailabilityResponse:
        """
        Check exact availability first.

        If no exact match exists, find the closest
        alternatives.
        """

        self._validate_request(request)

        exact_rooms = self.room_repository.find_available_rooms(
            check_in=request.check_in,
            check_out=request.check_out,
            bed_type=request.bed_type,
            breakfast=request.breakfast,
            guests=request.guests,
        )

        if exact_rooms:
            return AvailabilityResponse(
                status="exact_match",
                rooms=[
                    RoomAvailability(
                        room_id=room.id,
                        room_no=room.room_no,
                        room_type=room.room_type,
                        bed_type=room.bed_type,
                        breakfast=room.breakfast,
                        price_per_night=room.price_per_night,
                        floor=room.floor,
                        max_guests=room.max_guests,
                    )
                    for room in exact_rooms
                ],
                alternatives=[],
                message=(
                    f"Found {len(exact_rooms)} matching room(s)."
                ),
            )

        alternatives = self.alternative_service.find_alternatives(
            request=request,
            limit=2,
        )

        if alternatives:
            return AvailabilityResponse(
                status="alternatives",
                rooms=[],
                alternatives=alternatives,
                message=(
                    "No exact matching room is available. "
                    "Here are the closest alternatives."
                ),
            )

        return AvailabilityResponse(
            status="fully_booked",
            rooms=[],
            alternatives=[],
            message=(
                "No rooms are available for the requested "
                "dates and preferences."
            ),
        )

    @staticmethod
    def _validate_request(
        request: AvailabilityRequest,
    ) -> None:
        """
        Validate availability request.
        """

        if request.check_in < date.today():
            raise ValueError(
                "Check-in date cannot be in the past."
            )

        if request.check_out <= request.check_in:
            raise ValueError(
                "Check-out date must be after check-in date."
            )

        if request.guests < 1:
            raise ValueError(
                "Number of guests must be at least 1."
            )

