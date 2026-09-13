from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking


class BookingRepository:
    """
    Handles database operations related to bookings.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: int) -> Booking | None:
        """
        Retrieve a booking by database ID.
        """

        statement = select(Booking).where(
            Booking.id == booking_id
        )

        return self.db.execute(statement).scalar_one_or_none()

    def get_by_reference(
        self,
        booking_reference: str,
    ) -> Booking | None:
        """
        Retrieve a booking using its public booking reference.
        """

        statement = select(Booking).where(
            Booking.booking_reference == booking_reference
        )

        return self.db.execute(statement).scalar_one_or_none()

    def create(
        self,
        booking_reference: str,
        guest_id: int,
        reservation_id: int,
        status: str = "confirmed",
    ) -> Booking:
        """
        Create a booking record.
        """

        booking = Booking(
            booking_reference=booking_reference,
            guest_id=guest_id,
            reservation_id=reservation_id,
            status=status,
        )

        self.db.add(booking)
        self.db.flush()

        return booking