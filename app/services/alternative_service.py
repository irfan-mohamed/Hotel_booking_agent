from dataclasses import dataclass
from decimal import Decimal

from app.models import Room
from app.repositories.room_repository import RoomRepository
from app.schemas.availability import (
    AlternativeRoom,
    AvailabilityRequest,
)


@dataclass
class ScoredRoom:
    room: Room
    score: float
    differences: list[str]


class AlternativeService:
    """
    Finds and ranks alternatives when an exact room match
    is unavailable.
    """

    def __init__(
        self,
        room_repository: RoomRepository,
    ):
        self.room_repository = room_repository

    def find_alternatives(
        self,
        request: AvailabilityRequest,
        limit: int = 2,
    ) -> list[AlternativeRoom]:
        """
        Find and rank the closest available alternatives.
        """

        rooms = self.room_repository.get_available_rooms_for_alternative_search(
    check_in=request.check_in,
    check_out=request.check_out,
    guests=request.guests,
)

        scored_rooms = [
    self._score_room(
        room=room,
        request=request,
    )
    for room in rooms
    if not (
        room.bed_type == request.bed_type
        and room.breakfast == request.breakfast
    )
]

        scored_rooms.sort(
            key=lambda item: (
                -item.score,
                item.room.price_per_night,
                item.room.room_no,
            )
        )

        return [
            AlternativeRoom(
                room_id=item.room.id,
                room_no=item.room.room_no,
                room_type=item.room.room_type,
                bed_type=item.room.bed_type,
                breakfast=item.room.breakfast,
                price_per_night=item.room.price_per_night,
                floor=item.room.floor,
                max_guests=item.room.max_guests,
                match_score=item.score,
                differences=item.differences,
            )
            for item in scored_rooms[:limit]
        ]

    @staticmethod
    def _score_room(
        room: Room,
        request: AvailabilityRequest,
    ) -> ScoredRoom:
        """
        Calculate how closely a room matches the request.
        """

        score = 0.0
        differences: list[str] = []

        # Most important preference.
        if room.bed_type == request.bed_type:
            score += 50
        else:
            differences.append(
                f"bed type is {room.bed_type}"
            )

        # Breakfast preference.
        if room.breakfast == request.breakfast:
            score += 30
        else:
            if room.breakfast:
                differences.append(
                    "breakfast is included"
                )
            else:
                differences.append(
                    "breakfast is not included"
                )

        # Capacity should already be guaranteed by repository.
        if room.max_guests >= request.guests:
            score += 10

        # Room type isn't part of the original request,
        # so it is not heavily weighted.
        if room.room_type == "Standard":
            score += 5

        return ScoredRoom(
            room=room,
            score=score,
            differences=differences,
        )