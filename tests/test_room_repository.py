from datetime import timedelta

from app.models import Reservation


class TestRoomRepository:

    def test_get_room_by_id(
        self,
        db,
        room_repository,
        test_rooms,
    ):
        room = test_rooms[0]

        result = room_repository.get_by_id(room.id)

        assert result is not None
        assert result.room_no == 101

    def test_get_room_by_room_number(
        self,
        room_repository,
        test_rooms,
    ):
        result = room_repository.get_by_room_number(104)

        assert result is not None
        assert result.room_no == 104
        assert result.bed_type == "double"
        assert result.breakfast is True

    def test_get_all_rooms(
        self,
        room_repository,
        test_rooms,
    ):
        result = room_repository.get_all()

        assert len(result) == 8

        room_numbers = [
            room.room_no
            for room in result
        ]

        assert room_numbers == [
            101,
            102,
            103,
            104,
            201,
            202,
            203,
            301,
        ]

    def test_find_exact_available_room(
        self,
        room_repository,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        result = room_repository.find_available_rooms(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        room_numbers = {
            room.room_no
            for room in result
        }

        assert 104 in room_numbers
        assert 201 in room_numbers
        assert 301 in room_numbers

    def test_booked_room_is_excluded(
        self,
        db,
        room_repository,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        room = test_rooms[3]  # Room 104

        reservation = Reservation(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            status="confirmed",
        )

        db.add(reservation)
        db.flush()

        result = room_repository.find_available_rooms(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        room_numbers = {
            room.room_no
            for room in result
        }

        assert 104 not in room_numbers

    def test_adjacent_reservation_does_not_block_room(
        self,
        db,
        room_repository,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        room = test_rooms[3]  # Room 104

        reservation = Reservation(
            room_id=room.id,
            check_in=check_in - timedelta(days=3),
            check_out=check_in,
            status="confirmed",
        )

        db.add(reservation)
        db.flush()

        result = room_repository.find_available_rooms(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        room_numbers = {
            room.room_no
            for room in result
        }

        assert 104 in room_numbers

    def test_overlapping_reservation_blocks_room(
        self,
        db,
        room_repository,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        room = test_rooms[3]  # Room 104

        reservation = Reservation(
            room_id=room.id,
            check_in=check_in + timedelta(days=1),
            check_out=check_out + timedelta(days=1),
            status="confirmed",
        )

        db.add(reservation)
        db.flush()

        result = room_repository.find_available_rooms(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        room_numbers = {
            room.room_no
            for room in result
        }

        assert 104 not in room_numbers

    def test_cancelled_reservation_does_not_block_room(
        self,
        db,
        room_repository,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        room = test_rooms[3]  # Room 104

        reservation = Reservation(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            status="cancelled",
        )

        db.add(reservation)
        db.flush()

        result = room_repository.find_available_rooms(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        room_numbers = {
            room.room_no
            for room in result
        }

        assert 104 in room_numbers

    def test_guest_capacity_is_respected(
        self,
        room_repository,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        result = room_repository.find_available_rooms(
            check_in=check_in,
            check_out=check_out,
            bed_type="single",
            breakfast=False,
            guests=2,
        )

        assert result == []