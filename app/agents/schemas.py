from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal


class BookingRequirements(BaseModel):
    """
    Structured booking information extracted from the conversation.

    Every field is optional because the guest may provide the
    information over multiple conversational turns.
    """

    model_config = ConfigDict(extra="forbid")

    check_in: date | None = Field(
        default=None,
        description="Hotel check-in date.",
    )

    check_out: date | None = Field(
        default=None,
        description="Hotel check-out date.",
    )

    bed_type: Literal["single", "double"] | None = Field(
        default=None,
        description="Requested bed type.",
    )

    breakfast: bool | None = Field(
        default=None,
        description=(
            "Whether the guest wants breakfast included. "
            "True means breakfast is required."
        ),
    )

    guests: int | None = Field(
        default=None,
        ge=1,
        description="Number of guests staying in the room.",
    )


class GuestDetails(BaseModel):
    """
    Guest information required before booking.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        description="Full name of the guest.",
    )

    email: EmailStr | None = Field(
        default=None,
        description="Email address of the guest.",
    )


class AgentExtraction(BaseModel):
    """
    Structured information extracted from the latest user message.

    None means the user did not provide or modify that field.

    This distinction is important:
        breakfast=None
    does NOT mean breakfast=False.

    It means the latest message did not specify breakfast.
    """

    model_config = ConfigDict(extra="forbid")

    check_in: date | None = Field(
        default=None,
        description="New or updated check-in date, if provided.",
    )

    check_out: date | None = Field(
        default=None,
        description="New or updated check-out date, if provided.",
    )

    bed_type: Literal["single", "double"] | None = Field(
        default=None,
        description="New or updated bed type, if provided.",
    )

    breakfast: bool | None = Field(
        default=None,
        description="New or updated breakfast preference, if provided.",
    )

    guests: int | None = Field(
        default=None,
        ge=1,
        description="New or updated guest count, if provided.",
    )

    room_id: int | None = Field(
        default=None,
        description=(
            "Database room ID if the user explicitly selects "
            "a room from previously presented results."
        ),
    )

    room_no: int | None = Field(
        default=None,
        description=(
            "Human-facing room number if the user explicitly "
            "selects a room."
        ),
    )

    guest_name: str | None = Field(
        default=None,
        description="Guest name, if provided.",
    )

    guest_email: EmailStr | None = Field(
        default=None,
        description="Guest email, if provided.",
    )