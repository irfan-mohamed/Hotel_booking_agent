from app.schemas.availability import AvailabilityResponse


def resolve_selected_room(
    availability: AvailabilityResponse | None,
    room_no: int,
):
    """
    Resolve a human-facing room number against the rooms that were
    actually returned by the availability check.

    The LLM cannot select an arbitrary room that was not offered.
    """

    if availability is None:
        raise ValueError(
            "There is no current room availability result."
        )

    candidates = (
        availability.rooms
        if availability.status == "exact_match"
        else availability.alternatives
    )

    for room in candidates:
        if room.room_no == room_no:
            return room

    raise ValueError(
        f"Room {room_no} is not one of the currently available "
        "room options."
    )