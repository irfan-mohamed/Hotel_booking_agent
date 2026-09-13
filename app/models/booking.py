from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.guest import Guest
    from app.models.reservation import Reservation


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    booking_reference: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    guest_id: Mapped[int] = mapped_column(
        ForeignKey("guests.id"),
        nullable=False,
        index=True,
    )

    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="confirmed",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    guest: Mapped["Guest"] = relationship(
        "Guest",
        back_populates="bookings",
    )

    reservation: Mapped["Reservation"] = relationship(
        "Reservation",
        back_populates="booking",
    )

    def __repr__(self) -> str:
        return (
            f"<Booking("
            f"id={self.id}, "
            f"reference={self.booking_reference}, "
            f"guest_id={self.guest_id}, "
            f"reservation_id={self.reservation_id}, "
            f"status={self.status}"
            f")>"
        )