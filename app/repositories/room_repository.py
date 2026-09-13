from datetime import date

from sqlalchemy import and_, not_, or_, select
from sqlalchemy.orm import Session

from app.models import Reservation, Room


class RoomRepository:
    """
    Handles all database operations related to rooms.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, room_id: int) -> Room | None:
        """
        Retrieve a room by its database ID.
        """
        statement = select(Room).where(Room.id == room_id)

        return self.db.execute(statement).scalar_one_or_none()

    def get_by_room_number(self, room_no: int) -> Room | None:
        """
        Retrieve a room using the human-facing room number.
        """
        statement = select(Room).where(Room.room_no == room_no)

        return self.db.execute(statement).scalar_one_or_none()

    def get_all(self) -> list[Room]:
        """
        Retrieve all rooms.
        """
        statement = select(Room).order_by(Room.room_no)

        return list(self.db.execute(statement).scalars().all())

    def find_available_rooms(
        self,
        check_in: date,
        check_out: date,
        bed_type: str,
        breakfast: bool,
        guests: int,
    ) -> list[Room]:
        """
        Find rooms that:

        1. Match the requested bed type.
        2. Match the requested breakfast preference.
        3. Can accommodate the requested number of guests.
        4. Have no overlapping confirmed reservation.
        """

        overlapping_reservation = and_(
            Reservation.room_id == Room.id,
            Reservation.status == "confirmed",
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        )

        statement = (
            select(Room)
            .where(
                Room.bed_type == bed_type,
                Room.breakfast == breakfast,
                Room.max_guests >= guests,
                not_(
                    select(Reservation.id)
                    .where(overlapping_reservation)
                    .exists()
                ),
            )
            .order_by(
                Room.price_per_night.asc(),
                Room.room_no.asc(),
            )
        )

        return list(self.db.execute(statement).scalars().all())

    def find_available_rooms_by_preferences(
        self,
        check_in: date,
        check_out: date,
        bed_type: str | None,
        breakfast: bool | None,
        guests: int,
    ) -> list[Room]:
        """
        Find available rooms while allowing one or more preferences
        to be relaxed.

        This is primarily used by AlternativeService.
        """

        conditions = [
            Room.max_guests >= guests,
        ]

        if bed_type is not None:
            conditions.append(Room.bed_type == bed_type)

        if breakfast is not None:
            conditions.append(Room.breakfast == breakfast)

        overlapping_reservation = and_(
            Reservation.room_id == Room.id,
            Reservation.status == "confirmed",
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        )

        statement = (
            select(Room)
            .where(
                *conditions,
                not_(
                    select(Reservation.id)
                    .where(overlapping_reservation)
                    .exists()
                ),
            )
            .order_by(
                Room.price_per_night.asc(),
                Room.room_no.asc(),
            )
        )

        return list(self.db.execute(statement).scalars().all())

    def is_available(
        self,
        room_id: int,
        check_in: date,
        check_out: date,
    ) -> bool:
        """
        Check whether a specific room is available for a date range.
        """

        overlapping_reservation = (
            select(Reservation.id)
            .where(
                Reservation.room_id == room_id,
                Reservation.status == "confirmed",
                Reservation.check_in < check_out,
                Reservation.check_out > check_in,
            )
            .exists()
        )

        statement = select(not_(overlapping_reservation))

        return bool(self.db.execute(statement).scalar_one())

    def get_available_rooms_for_alternative_search(
        self,
        check_in: date,
        check_out: date,
        guests: int,
    ) -> list[Room]:
        """
        Return all rooms that can accommodate the guest and are
        available for the requested dates.

        AlternativeService performs the preference scoring.
        """

        overlapping_reservation = and_(
            Reservation.room_id == Room.id,
            Reservation.status == "confirmed",
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        )

        statement = (
            select(Room)
            .where(
                Room.max_guests >= guests,
                not_(
                    select(Reservation.id)
                    .where(overlapping_reservation)
                    .exists()
                ),
            )
            .order_by(
                Room.price_per_night.asc(),
                Room.room_no.asc(),
            )
        )

        return list(self.db.execute(statement).scalars().all())