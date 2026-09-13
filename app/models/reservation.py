from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.room import Room


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False,
        index=True,
    )

    check_in: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    check_out: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="confirmed",
        index=True,
    )

    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="reservations",
    )

    booking: Mapped["Booking | None"] = relationship(
        "Booking",
        back_populates="reservation",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Reservation("
            f"id={self.id}, "
            f"room_id={self.room_id}, "
            f"check_in={self.check_in}, "
            f"check_out={self.check_out}, "
            f"status={self.status}"
            f")>"
        )