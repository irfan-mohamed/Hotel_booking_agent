from datetime import date

from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService


class BookingTool:
    """
    Tool boundary between the conversational agent
    and the booking business service.

    The tool is intentionally thin:

        Agent
            ↓
        BookingTool
            ↓
        BookingService
            ↓
        Repositories
            ↓
        PostgreSQL
    """

    def __init__(
        self,
        booking_service: BookingService,
    ):
        self.booking_service = booking_service

    def create_booking(
        self,
        room_id: int,
        check_in: date,
        check_out: date,
        guests: int,
        guest_name: str,
        guest_email: str,
    ) -> BookingResponse:
        """
        Create a hotel booking.

        The BookingService performs the final availability
        check, capacity validation, guest creation/reuse,
        reservation creation, booking creation, and database
        transaction.

        Args:
            room_id:
                Database ID of the selected room.

            check_in:
                Guest check-in date.

            check_out:
                Guest check-out date.

            guests:
                Number of guests staying.

            guest_name:
                Full name of the guest.

            guest_email:
                Email address of the guest.

        Returns:
            BookingResponse containing the booking reference,
            guest information, room information, stay details,
            and total price.

        Raises:
            ValueError:
                If the room does not exist, is unavailable,
                cannot accommodate the guests, or the dates
                are invalid.
        """

        request = BookingCreate(
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            guest_name=guest_name,
            guest_email=guest_email,
        )

        return self.booking_service.create_booking(
            request
        )


def create_booking(
    booking_service: BookingService,
    room_id: int,
    check_in: date,
    check_out: date,
    guests: int,
    guest_name: str,
    guest_email: str,
) -> BookingResponse:
    """
    Function-style wrapper around BookingTool.

    This interface is useful when exposing the booking
    capability to an LLM framework that expects a
    callable tool function.
    """

    tool = BookingTool(
        booking_service=booking_service,
    )

    return tool.create_booking(
        room_id=room_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        guest_name=guest_name,
        guest_email=guest_email,
    )
