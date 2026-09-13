from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="guest",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Guest("
            f"id={self.id}, "
            f"name={self.name}, "
            f"email={self.email}"
            f")>"
        )