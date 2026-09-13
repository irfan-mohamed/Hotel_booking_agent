from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.availability import AvailabilityRequest


class TestAvailabilityService:

    def test_exact_match(
        self,
        availability_service,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        request = AvailabilityRequest(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        result = availability_service.check_availability(
            request
        )

        assert result.status == "exact_match"
        assert len(result.rooms) > 0
        assert result.alternatives == []

    def test_exact_match_contains_requested_preferences(
        self,
        availability_service,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        request = AvailabilityRequest(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        result = availability_service.check_availability(
            request
        )

        for room in result.rooms:
            assert room.bed_type == "double"
            assert room.breakfast is True
            assert room.max_guests >= 2

    def test_no_exact_match_returns_alternatives(
        self,
        db,
        availability_service,
        test_rooms,
        future_dates,
    ):
        from app.models import Reservation

        check_in, check_out = future_dates

        exact_rooms = [
            room
            for room in test_rooms
            if room.bed_type == "double"
            and room.breakfast is True
        ]

        for room in exact_rooms:
            db.add(
                Reservation(
                    room_id=room.id,
                    check_in=check_in,
                    check_out=check_out,
                    status="confirmed",
                )
            )

        db.flush()

        request = AvailabilityRequest(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        result = availability_service.check_availability(
            request
        )

        assert result.status == "alternatives"
        assert result.rooms == []
        assert len(result.alternatives) > 0

    def test_fully_booked(
        self,
        db,
        availability_service,
        test_rooms,
        future_dates,
    ):
        from app.models import Reservation

        check_in, check_out = future_dates

        for room in test_rooms:
            db.add(
                Reservation(
                    room_id=room.id,
                    check_in=check_in,
                    check_out=check_out,
                    status="confirmed",
                )
            )

        db.flush()

        request = AvailabilityRequest(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        result = availability_service.check_availability(
            request
        )

        assert result.status == "fully_booked"
        assert result.rooms == []
        assert result.alternatives == []

    def test_past_check_in_is_rejected(
        self,
        availability_service,
    ):
        request = AvailabilityRequest(
            check_in=date.today() - timedelta(days=1),
            check_out=date.today() + timedelta(days=2),
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        with pytest.raises(ValueError):
            availability_service.check_availability(request)

    def test_invalid_date_range_is_rejected(
        self,
    ):
        with pytest.raises(ValidationError):
            AvailabilityRequest(
                check_in=date.today() + timedelta(days=5),
                check_out=date.today() + timedelta(days=2),
                bed_type="double",
                breakfast=True,
                guests=2,
            )

    def test_same_day_checkout_is_rejected(
        self,
    ):
        check_in = date.today() + timedelta(days=5)

        with pytest.raises(ValidationError):
            AvailabilityRequest(
                check_in=check_in,
                check_out=check_in,
                bed_type="double",
                breakfast=True,
                guests=2,
            )

    def test_invalid_guest_count_is_rejected(
        self,
    ):
        check_in = date.today() + timedelta(days=5)
        check_out = check_in + timedelta(days=2)

        with pytest.raises(ValidationError):
            AvailabilityRequest(
                check_in=check_in,
                check_out=check_out,
                bed_type="double",
                breakfast=True,
                guests=0,
            )