class TestBookingRepository:

    def test_create_booking(
        self,
        booking_repository,
        guest_repository,
        db,
        test_rooms,
    ):
        from app.models import Reservation

        guest = guest_repository.create(
            name="Booking User",
            email="booking@example.com",
        )

        reservation = Reservation(
            room_id=test_rooms[0].id,
            check_in="2030-01-10",
            check_out="2030-01-12",
            status="confirmed",
        )

        db.add(reservation)
        db.flush()

        booking = booking_repository.create(
            booking_reference="HTL-TEST001",
            guest_id=guest.id,
            reservation_id=reservation.id,
        )

        assert booking.id is not None
        assert booking.booking_reference == "HTL-TEST001"
        assert booking.status == "confirmed"

    def test_get_booking_by_reference(
        self,
        booking_repository,
        guest_repository,
        db,
        test_rooms,
    ):
        from app.models import Reservation

        guest = guest_repository.create(
            name="Reference User",
            email="reference@example.com",
        )

        reservation = Reservation(
            room_id=test_rooms[0].id,
            check_in="2030-02-10",
            check_out="2030-02-12",
            status="confirmed",
        )

        db.add(reservation)
        db.flush()

        created = booking_repository.create(
            booking_reference="HTL-REF001",
            guest_id=guest.id,
            reservation_id=reservation.id,
        )

        result = booking_repository.get_by_reference(
            "HTL-REF001"
        )

        assert result is not None
        assert result.id == created.id

    def test_missing_booking_returns_none(
        self,
        booking_repository,
    ):
        result = booking_repository.get_by_reference(
            "DOES-NOT-EXIST"
        )

        assert result is None