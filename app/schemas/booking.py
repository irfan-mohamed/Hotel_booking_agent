from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, model_validator


class GuestCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    email: EmailStr


class BookingCreate(BaseModel):
    room_id: int

    check_in: date

    check_out: date

    guests: int = Field(
        ...,
        ge=1,
    )

    guest_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    guest_email: EmailStr

    @model_validator(mode="after")
    def validate_dates(self) -> "BookingCreate":
        if self.check_in < date.today():
            raise ValueError(
                "Check-in date cannot be in the past."
            )

        if self.check_out <= self.check_in:
            raise ValueError(
                "Check-out date must be after check-in date."
            )

        return self


class BookingResponse(BaseModel):
    booking_reference: str

    guest_name: str

    guest_email: EmailStr

    room_no: int

    room_type: str

    bed_type: str

    breakfast: bool

    check_in: date

    check_out: date

    nights: int

    price_per_night: Decimal

    total_price: Decimal

    status: str
