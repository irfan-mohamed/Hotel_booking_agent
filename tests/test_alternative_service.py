from app.schemas.availability import AvailabilityRequest


class TestAlternativeService:

    def test_same_bed_without_breakfast_is_preferred(
        self,
        alternative_service,
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

        alternatives = alternative_service.find_alternatives(
            request=request,
            limit=2,
        )

        assert len(alternatives) > 0

        room_numbers = [
            room.room_no
            for room in alternatives
        ]

        # Room 103 = same bed, breakfast differs.
        # It should rank above a single-bed alternative.
        assert 103 in room_numbers

    def test_alternatives_are_limited(
        self,
        alternative_service,
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

        alternatives = alternative_service.find_alternatives(
            request=request,
            limit=1,
        )

        assert len(alternatives) <= 1

    def test_alternative_has_difference_description(
        self,
        alternative_service,
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

        alternatives = alternative_service.find_alternatives(
            request=request,
            limit=2,
        )

        for alternative in alternatives:
            assert isinstance(
                alternative.differences,
                list,
            )

    def test_capacity_is_respected(
        self,
        alternative_service,
        test_rooms,
        future_dates,
    ):
        check_in, check_out = future_dates

        request = AvailabilityRequest(
            check_in=check_in,
            check_out=check_out,
            bed_type="single",
            breakfast=True,
            guests=4,
        )

        alternatives = alternative_service.find_alternatives(
            request=request,
            limit=2,
        )

        for alternative in alternatives:
            assert alternative.max_guests >= 4