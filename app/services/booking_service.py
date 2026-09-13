from datetime import date
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Reservation
from app.repositories.booking_repository import BookingRepository
from app.repositories.guest_repository import GuestRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
)


class BookingService:
    """
    Handles the complete booking workflow.
    """

    def __init__(
        self,
        db: Session,
        room_repository: RoomRepository,
        guest_repository: GuestRepository,
        booking_repository: BookingRepository,
    ):
        self.db = db
        self.room_repository = room_repository
        self.guest_repository = guest_repository
        self.booking_repository = booking_repository

    def create_booking(
        self,
        request: BookingCreate,
    ) -> BookingResponse:
        """
        Create a guest, reservation and booking as one
        database transaction.

        Availability is re-checked before booking.
        """

        self._validate_request(request)

        try:
            # --------------------------------------------------
            # 1. Retrieve room
            # --------------------------------------------------

            room = self.room_repository.get_by_id(
                request.room_id
            )

            if room is None:
                raise ValueError(
                    "The requested room does not exist."
                )

            # --------------------------------------------------
            # 2. Re-check availability
            # --------------------------------------------------

            available = self.room_repository.is_available(
                room_id=room.id,
                check_in=request.check_in,
                check_out=request.check_out,
            )

            if not available:
                raise ValueError(
                    "The selected room is no longer available "
                    "for the requested dates."
                )

            # --------------------------------------------------
            # 3. Check capacity
            # --------------------------------------------------

            if room.max_guests < request.guests:
                raise ValueError(
                    "The selected room cannot accommodate "
                    "the requested number of guests."
                )

            # --------------------------------------------------
            # 4. Create or retrieve guest
            # --------------------------------------------------

            guest = self.guest_repository.get_or_create(
                name=request.guest_name,
                email=str(request.guest_email),
            )

            # --------------------------------------------------
            # 5. Create reservation
            # --------------------------------------------------

            reservation = Reservation(
                room_id=room.id,
                check_in=request.check_in,
                check_out=request.check_out,
                status="confirmed",
            )

            self.db.add(reservation)

            # Get reservation.id without committing.
            self.db.flush()

            # --------------------------------------------------
            # 6. Generate booking reference
            # --------------------------------------------------

            booking_reference = self._generate_booking_reference()

            # --------------------------------------------------
            # 7. Create booking
            # --------------------------------------------------

            booking = self.booking_repository.create(
                booking_reference=booking_reference,
                guest_id=guest.id,
                reservation_id=reservation.id,
                status="confirmed",
            )

            # --------------------------------------------------
            # 8. Commit EVERYTHING together
            # --------------------------------------------------

            self.db.commit()

            # Refresh so generated fields such as created_at
            # are available.
            self.db.refresh(booking)

            nights = (
                request.check_out - request.check_in
            ).days

            total_price = (
                room.price_per_night * nights
            )

            return BookingResponse(
                booking_reference=booking.booking_reference,
                guest_name=guest.name,
                guest_email=guest.email,
                room_no=room.room_no,
                room_type=room.room_type,
                bed_type=room.bed_type,
                breakfast=room.breakfast,
                check_in=request.check_in,
                check_out=request.check_out,
                nights=nights,
                price_per_night=room.price_per_night,
                total_price=total_price,
                status=booking.status,
            )

        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _generate_booking_reference() -> str:
        """
        Generate a human-readable unique booking reference.
        """

        return f"HTL-{uuid4().hex[:10].upper()}"

    @staticmethod
    def _validate_request(
        request: BookingCreate,
    ) -> None:
        """
        Validate booking input.
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

        if not request.guest_name.strip():
            raise ValueError(
                "Guest name cannot be empty."
            )