from datetime import date, timedelta

import pytest

from app.schemas.booking import BookingCreate


class TestBookingService:

    def test_create_booking_successfully(
        self,
        booking_service,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        room = next(
            room
            for room in test_rooms
            if room.room_no == 104
        )

        request = BookingCreate(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="John Doe",
            guest_email="john@example.com",
        )

        result = booking_service.create_booking(
            request
        )

        assert result.booking_reference.startswith(
            "HTL-"
        )

        assert result.guest_name == "John Doe"
        assert result.guest_email == "john@example.com"

        assert result.room_no == 104
        assert result.room_type == "Standard"
        assert result.bed_type == "double"
        assert result.breakfast is True

        assert result.nights == 3
        assert result.price_per_night == 3400
        assert result.total_price == 10200

        assert result.status == "confirmed"

    def test_booking_creates_guest(
        self,
        booking_service,
        guest_repository,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        room = test_rooms[3]

        request = BookingCreate(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="Guest Created",
            guest_email="created@example.com",
        )

        booking_service.create_booking(request)

        guest = guest_repository.get_by_email(
            "created@example.com"
        )

        assert guest is not None
        assert guest.name == "Guest Created"

    def test_existing_guest_is_reused(
        self,
        booking_service,
        guest_repository,
        test_rooms,
    ):
        check_in = date.today() + timedelta(days=40)
        check_out = check_in + timedelta(days=2)

        existing_guest = guest_repository.create(
            name="Existing Guest",
            email="existing@example.com",
        )

        room = test_rooms[3]

        request = BookingCreate(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
        )

        booking_service.create_booking(request)

        guest = guest_repository.get_by_email(
            "existing@example.com"
        )

        assert guest.id == existing_guest.id

    def test_unavailable_room_is_rejected(
        self,
        db,
        booking_service,
        test_rooms,
        future_dates,
    ):
        from app.models import Reservation

        check_in, check_out = future_dates

        room = test_rooms[3]

        db.add(
            Reservation(
                room_id=room.id,
                check_in=check_in,
                check_out=check_out,
                status="confirmed",
            )
        )

        db.flush()

        request = BookingCreate(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="Blocked Guest",
            guest_email="blocked@example.com",
        )

        with pytest.raises(ValueError, match="no longer available"):
            booking_service.create_booking(request)

    def test_nonexistent_room_is_rejected(
        self,
        booking_service,
        future_dates,
    ):
        check_in, check_out = future_dates

        request = BookingCreate(
            room_id=999999,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="Missing Room",
            guest_email="missing@example.com",
        )

        with pytest.raises(ValueError, match="does not exist"):
            booking_service.create_booking(request)

    def test_room_capacity_is_enforced(
        self,
        booking_service,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        room = next(
            room
            for room in test_rooms
            if room.room_no == 104
        )

        request = BookingCreate(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=3,
            guest_name="Too Many Guests",
            guest_email="capacity@example.com",
        )

        with pytest.raises(ValueError, match="cannot accommodate"):
            booking_service.create_booking(request)

    def test_past_booking_is_rejected(
        self,
        booking_service,
        test_rooms,
    ):
        check_in = date.today() - timedelta(days=5)
        check_out = date.today() - timedelta(days=2)

        room = test_rooms[3]

        request = BookingCreate(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="Past Guest",
            guest_email="past@example.com",
        )

        with pytest.raises(ValueError, match="past"):
            booking_service.create_booking(request)

    def test_invalid_booking_dates_are_rejected(
        self,
        booking_service,
        test_rooms,
    ):
        check_in = date.today() + timedelta(days=10)
        check_out = check_in

        room = test_rooms[3]

        request = BookingCreate(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="Invalid Date",
            guest_email="invalid@example.com",
        )

        with pytest.raises(ValueError, match="after check-in"):
            booking_service.create_booking(request)

    def test_booking_reference_is_unique(
        self,
        booking_service,
        test_rooms,
    ):
        check_in_1 = date.today() + timedelta(days=50)
        check_out_1 = check_in_1 + timedelta(days=2)

        check_in_2 = date.today() + timedelta(days=60)
        check_out_2 = check_in_2 + timedelta(days=2)

        room_1 = test_rooms[3]
        room_2 = test_rooms[4]

        request_1 = BookingCreate(
            room_id=room_1.id,
            check_in=check_in_1,
            check_out=check_out_1,
            guests=2,
            guest_name="Guest One",
            guest_email="one@example.com",
        )

        request_2 = BookingCreate(
            room_id=room_2.id,
            check_in=check_in_2,
            check_out=check_out_2,
            guests=2,
            guest_name="Guest Two",
            guest_email="two@example.com",
        )

        booking_1 = booking_service.create_booking(
            request_1
        )

        booking_2 = booking_service.create_booking(
            request_2
        )

        assert (
            booking_1.booking_reference
            != booking_2.booking_reference
        )