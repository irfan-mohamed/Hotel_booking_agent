from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.schemas.availability import (
    AlternativeRoom,
    AvailabilityRequest,
    AvailabilityResponse,
    RoomAvailability,
)
from app.services.availability_service import AvailabilityService
from app.tools.availability_tool import (
    AvailabilityTool,
    check_room_availability,
)


class TestAvailabilityTool:
    """
    Tests for the AvailabilityTool boundary.

    These tests mock AvailabilityService so that the tool
    can be tested independently from PostgreSQL and the
    repository layer.
    """

    @pytest.fixture
    def availability_service(self):
        """
        Mock AvailabilityService.
        """
        return Mock(spec=AvailabilityService)

    @pytest.fixture
    def availability_tool(self, availability_service):
        """
        Create AvailabilityTool using the mocked service.
        """
        return AvailabilityTool(
            availability_service=availability_service,
        )

    @pytest.fixture
    def future_dates(self):
        """
        Return a valid future stay.
        """
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=3)

        return check_in, check_out

    # ---------------------------------------------------------
    # Exact Match
    # ---------------------------------------------------------

    def test_exact_match_is_returned(
        self,
        availability_tool,
        availability_service,
        future_dates,
    ):
        """
        The tool should return the exact-match response
        produced by AvailabilityService.
        """

        check_in, check_out = future_dates

        room = RoomAvailability(
            room_id=1,
            room_no=104,
            room_type="Standard",
            bed_type="double",
            breakfast=True,
            price_per_night=Decimal("3400"),
            floor=1,
            max_guests=2,
        )

        expected_response = AvailabilityResponse(
            status="exact_match",
            rooms=[room],
            alternatives=[],
            message="Found 1 matching room(s).",
        )

        availability_service.check_availability.return_value = (
            expected_response
        )

        result = availability_tool.check_room_availability(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        assert result == expected_response
        assert result.status == "exact_match"
        assert len(result.rooms) == 1
        assert result.rooms[0].room_no == 104

    def test_exact_match_request_is_constructed_correctly(
        self,
        availability_tool,
        availability_service,
        future_dates,
    ):
        """
        Verify that the tool converts primitive arguments
        into the correct AvailabilityRequest before passing
        it to the service.
        """

        check_in, check_out = future_dates

        availability_service.check_availability.return_value = (
            AvailabilityResponse(
                status="fully_booked",
                rooms=[],
                alternatives=[],
                message="No rooms available.",
            )
        )

        availability_tool.check_room_availability(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        availability_service.check_availability.assert_called_once()

        request = (
            availability_service
            .check_availability
            .call_args
            .args[0]
        )

        assert isinstance(request, AvailabilityRequest)
        assert request.check_in == check_in
        assert request.check_out == check_out
        assert request.bed_type == "double"
        assert request.breakfast is True
        assert request.guests == 2

    # ---------------------------------------------------------
    # Alternatives
    # ---------------------------------------------------------

    def test_alternatives_are_returned(
        self,
        availability_tool,
        availability_service,
        future_dates,
    ):
        """
        The tool should pass alternative results through
        unchanged.
        """

        check_in, check_out = future_dates

        alternative = AlternativeRoom(
            room_id=1,
            room_no=103,
            room_type="Standard",
            bed_type="double",
            breakfast=False,
            price_per_night=Decimal("3000"),
            floor=1,
            max_guests=2,
            match_score=60.0,
            differences=[
                "breakfast is not included",
            ],
        )

        expected_response = AvailabilityResponse(
            status="alternatives",
            rooms=[],
            alternatives=[alternative],
            message=(
                "No exact matching room is available. "
                "Here are the closest alternatives."
            ),
        )

        availability_service.check_availability.return_value = (
            expected_response
        )

        result = availability_tool.check_room_availability(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        assert result.status == "alternatives"
        assert len(result.alternatives) == 1
        assert result.alternatives[0].room_no == 103
        assert result.alternatives[0].breakfast is False

    # ---------------------------------------------------------
    # Fully Booked
    # ---------------------------------------------------------

    def test_fully_booked_response_is_returned(
        self,
        availability_tool,
        availability_service,
        future_dates,
    ):
        """
        The tool should correctly return the fully-booked
        response from the service.
        """

        check_in, check_out = future_dates

        expected_response = AvailabilityResponse(
            status="fully_booked",
            rooms=[],
            alternatives=[],
            message=(
                "No rooms are available for the requested "
                "dates and preferences."
            ),
        )

        availability_service.check_availability.return_value = (
            expected_response
        )

        result = availability_tool.check_room_availability(
            check_in=check_in,
            check_out=check_out,
            bed_type="double",
            breakfast=True,
            guests=2,
        )

        assert result.status == "fully_booked"
        assert result.rooms == []
        assert result.alternatives == []

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_invalid_date_range_is_rejected(
        self,
        availability_tool,
        availability_service,
    ):
        """
        Check-out must be after check-in.
        """

        check_in = date.today() + timedelta(days=30)
        check_out = check_in

        with pytest.raises(ValueError):
            availability_tool.check_room_availability(
                check_in=check_in,
                check_out=check_out,
                bed_type="double",
                breakfast=True,
                guests=2,
            )

        availability_service.check_availability.assert_not_called()

    def test_past_check_in_is_rejected_by_service(
        self,
        availability_tool,
        availability_service,
    ):
        """
        Past dates are handled by AvailabilityService.

        The tool should construct the request and delegate
        the business validation to the service.
        """

        past_date = date.today() - timedelta(days=1)
        check_out = date.today() + timedelta(days=2)

        availability_service.check_availability.side_effect = (
            ValueError(
                "Check-in date cannot be in the past."
            )
        )

        with pytest.raises(
            ValueError,
            match="Check-in date cannot be in the past",
        ):
            availability_tool.check_room_availability(
                check_in=past_date,
                check_out=check_out,
                bed_type="double",
                breakfast=True,
                guests=2,
            )

    def test_invalid_guest_count_is_rejected(
        self,
        availability_tool,
        availability_service,
    ):
        """
        Guest count must be at least 1.

        Pydantic validates this before the service is called.
        """

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=3)

        with pytest.raises(ValueError):
            availability_tool.check_room_availability(
                check_in=check_in,
                check_out=check_out,
                bed_type="double",
                breakfast=True,
                guests=0,
            )

        availability_service.check_availability.assert_not_called()

    def test_invalid_bed_type_is_rejected(
        self,
        availability_tool,
        availability_service,
        future_dates,
    ):
        """
        Only single and double bed types are accepted.
        """

        check_in, check_out = future_dates

        with pytest.raises(ValueError):
            availability_tool.check_room_availability(
                check_in=check_in,
                check_out=check_out,
                bed_type="king",
                breakfast=True,
                guests=2,
            )

        availability_service.check_availability.assert_not_called()

    # ---------------------------------------------------------
    # Service interaction
    # ---------------------------------------------------------

    def test_service_is_called_exactly_once(
        self,
        availability_tool,
        availability_service,
        future_dates,
    ):
        """
        Every room availability request must invoke the
        availability service exactly once.
        """

        check_in, check_out = future_dates

        availability_service.check_availability.return_value = (
            AvailabilityResponse(
                status="fully_booked",
                rooms=[],
                alternatives=[],
                message="No rooms available.",
            )
        )

        availability_tool.check_room_availability(
            check_in=check_in,
            check_out=check_out,
            bed_type="single",
            breakfast=False,
            guests=1,
        )

        availability_service.check_availability.assert_called_once()

    # ---------------------------------------------------------
    # Function-style wrapper
    # ---------------------------------------------------------

    def test_function_wrapper_returns_service_response(
        self,
        availability_service,
        future_dates,
    ):
        """
        Verify that the function-style tool interface works.

        This interface will be useful when integrating with
        an LLM framework.
        """

        check_in, check_out = future_dates

        expected_response = AvailabilityResponse(
            status="exact_match",
            rooms=[],
            alternatives=[],
            message="Found matching room.",
        )

        availability_service.check_availability.return_value = (
            expected_response
        )

        result = check_room_availability(
            availability_service=availability_service,
            check_in=check_in,
            check_out=check_out,
            bed_type="single",
            breakfast=False,
            guests=1,
        )

        assert result == expected_response
        availability_service.check_availability.assert_called_once()
