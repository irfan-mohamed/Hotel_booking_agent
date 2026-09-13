from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.reservation import Reservation


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    room_no: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
    )

    room_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    bed_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    breakfast: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    price_per_night: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    floor: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    max_guests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Room("
            f"room_no={self.room_no}, "
            f"type={self.room_type}, "
            f"bed={self.bed_type}, "
            f"breakfast={self.breakfast}"
            f")>"
        )