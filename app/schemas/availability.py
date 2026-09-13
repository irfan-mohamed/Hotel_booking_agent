from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AvailabilityRequest(BaseModel):
    check_in: date
    check_out: date
    bed_type: Literal["single", "double"]
    breakfast: bool
    guests: int = Field(
        ...,
        ge=1,
        description="Number of guests staying in the room.",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "AvailabilityRequest":
        if self.check_out <= self.check_in:
            raise ValueError(
                "Check-out date must be after check-in date."
            )

        return self


class RoomAvailability(BaseModel):
    room_id: int
    room_no: int
    room_type: str
    bed_type: str
    breakfast: bool
    price_per_night: Decimal
    floor: int
    max_guests: int

    model_config = {
        "from_attributes": True,
    }


class AlternativeRoom(BaseModel):
    room_id: int
    room_no: int
    room_type: str
    bed_type: str
    breakfast: bool
    price_per_night: Decimal
    floor: int
    max_guests: int
    match_score: float
    differences: list[str]

    model_config = {
        "from_attributes": True,
    }


class AvailabilityResponse(BaseModel):
    status: Literal[
        "exact_match",
        "alternatives",
        "fully_booked",
    ]

    rooms: list[RoomAvailability] = Field(
        default_factory=list,
    )

    alternatives: list[AlternativeRoom] = Field(
        default_factory=list,
    )

    message: str | None = None