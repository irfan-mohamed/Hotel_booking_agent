from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService
from app.tools.booking_tool import (
    BookingTool,
    create_booking,
)


class TestBookingTool:
    """
    Tests for the BookingTool boundary.

    BookingService is mocked so these tests do not depend
    on PostgreSQL or the repository layer.
    """

    @pytest.fixture
    def booking_service(self):
        """
        Mock BookingService.
        """
        return Mock(spec=BookingService)

    @pytest.fixture
    def booking_tool(self, booking_service):
        """
        Create BookingTool using the mocked service.
        """
        return BookingTool(
            booking_service=booking_service,
        )

    @pytest.fixture
    def future_dates(self):
        """
        Return a valid future stay.
        """
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=3)

        return check_in, check_out

    @pytest.fixture
    def expected_booking_response(self, future_dates):
        """
        Example successful booking response.
        """
        check_in, check_out = future_dates

        return BookingResponse(
            booking_reference="HTL-ABC1234567",
            guest_name="John Doe",
            guest_email="john@example.com",
            room_no=104,
            room_type="Standard",
            bed_type="double",
            breakfast=True,
            check_in=check_in,
            check_out=check_out,
            nights=3,
            price_per_night=Decimal("3400"),
            total_price=Decimal("10200"),
            status="confirmed",
        )

    # ---------------------------------------------------------
    # Successful Booking
    # ---------------------------------------------------------

    def test_booking_is_created_successfully(
        self,
        booking_tool,
        booking_service,
        future_dates,
        expected_booking_response,
    ):
        """
        The tool should return the BookingResponse generated
        by BookingService.
        """

        check_in, check_out = future_dates

        booking_service.create_booking.return_value = (
            expected_booking_response
        )

        result = booking_tool.create_booking(
            room_id=4,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="John Doe",
            guest_email="john@example.com",
        )

        assert result == expected_booking_response
        assert result.booking_reference == "HTL-ABC1234567"
        assert result.status == "confirmed"
        assert result.room_no == 104
        assert result.nights == 3
        assert result.total_price == Decimal("10200")

    # ---------------------------------------------------------
    # Request Construction
    # ---------------------------------------------------------

    def test_booking_request_is_constructed_correctly(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        Verify that primitive tool arguments are converted
        into a BookingCreate request before reaching the
        service.
        """

        check_in, check_out = future_dates

        booking_service.create_booking.return_value = (
            Mock(spec=BookingResponse)
        )

        booking_tool.create_booking(
            room_id=4,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="John Doe",
            guest_email="john@example.com",
        )

        booking_service.create_booking.assert_called_once()

        request = (
            booking_service
            .create_booking
            .call_args
            .args[0]
        )

        assert isinstance(request, BookingCreate)
        assert request.room_id == 4
        assert request.check_in == check_in
        assert request.check_out == check_out
        assert request.guests == 2
        assert request.guest_name == "John Doe"
        assert str(request.guest_email) == "john@example.com"

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_invalid_date_range_is_rejected(
        self,
        booking_tool,
        booking_service,
    ):
        """
        Check-out must be after check-in.
        """

        check_in = date.today() + timedelta(days=30)
        check_out = check_in

        with pytest.raises(ValueError):
            booking_tool.create_booking(
                room_id=4,
                check_in=check_in,
                check_out=check_out,
                guests=2,
                guest_name="John Doe",
                guest_email="john@example.com",
            )

        booking_service.create_booking.assert_not_called()

    def test_invalid_guest_count_is_rejected(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        Guest count must be at least 1.
        """

        check_in, check_out = future_dates

        with pytest.raises(ValueError):
            booking_tool.create_booking(
                room_id=4,
                check_in=check_in,
                check_out=check_out,
                guests=0,
                guest_name="John Doe",
                guest_email="john@example.com",
            )

        booking_service.create_booking.assert_not_called()

    def test_invalid_email_is_rejected(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        EmailStr validation should reject malformed email
        addresses before the booking service is called.
        """

        check_in, check_out = future_dates

        with pytest.raises(ValueError):
            booking_tool.create_booking(
                room_id=4,
                check_in=check_in,
                check_out=check_out,
                guests=2,
                guest_name="John Doe",
                guest_email="not-an-email",
            )

        booking_service.create_booking.assert_not_called()

    def test_empty_guest_name_is_rejected(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        Guest name must satisfy BookingCreate validation.
        """

        check_in, check_out = future_dates

        with pytest.raises(ValueError):
            booking_tool.create_booking(
                room_id=4,
                check_in=check_in,
                check_out=check_out,
                guests=2,
                guest_name="",
                guest_email="john@example.com",
            )

        booking_service.create_booking.assert_not_called()

    def test_short_guest_name_is_rejected(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        Guest names shorter than two characters are rejected.
        """

        check_in, check_out = future_dates

        with pytest.raises(ValueError):
            booking_tool.create_booking(
                room_id=4,
                check_in=check_in,
                check_out=check_out,
                guests=2,
                guest_name="J",
                guest_email="john@example.com",
            )

        booking_service.create_booking.assert_not_called()

    # ---------------------------------------------------------
    # Service Errors
    # ---------------------------------------------------------

    def test_unavailable_room_error_is_propagated(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        BookingService is responsible for the final
        availability check.

        The tool should not swallow that error.
        """

        check_in, check_out = future_dates

        booking_service.create_booking.side_effect = ValueError(
            "The selected room is no longer available "
            "for the requested dates."
        )

        with pytest.raises(
            ValueError,
            match="no longer available",
        ):
            booking_tool.create_booking(
                room_id=4,
                check_in=check_in,
                check_out=check_out,
                guests=2,
                guest_name="John Doe",
                guest_email="john@example.com",
            )

    def test_nonexistent_room_error_is_propagated(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        Errors from BookingService should be propagated
        to the caller.
        """

        check_in, check_out = future_dates

        booking_service.create_booking.side_effect = ValueError(
            "The requested room does not exist."
        )

        with pytest.raises(
            ValueError,
            match="room does not exist",
        ):
            booking_tool.create_booking(
                room_id=99999,
                check_in=check_in,
                check_out=check_out,
                guests=2,
                guest_name="John Doe",
                guest_email="john@example.com",
            )

    def test_capacity_error_is_propagated(
        self,
        booking_tool,
        booking_service,
        future_dates,
    ):
        """
        Capacity validation belongs to BookingService.
        """

        check_in, check_out = future_dates

        booking_service.create_booking.side_effect = ValueError(
            "The selected room cannot accommodate "
            "the requested number of guests."
        )

        with pytest.raises(
            ValueError,
            match="cannot accommodate",
        ):
            booking_tool.create_booking(
                room_id=4,
                check_in=check_in,
                check_out=check_out,
                guests=10,
                guest_name="John Doe",
                guest_email="john@example.com",
            )

    # ---------------------------------------------------------
    # Service Interaction
    # ---------------------------------------------------------

    def test_service_is_called_exactly_once(
        self,
        booking_tool,
        booking_service,
        future_dates,
        expected_booking_response,
    ):
        """
        Every valid booking request should invoke the
        BookingService exactly once.
        """

        check_in, check_out = future_dates

        booking_service.create_booking.return_value = (
            expected_booking_response
        )

        booking_tool.create_booking(
            room_id=4,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="John Doe",
            guest_email="john@example.com",
        )

        booking_service.create_booking.assert_called_once()

    # ---------------------------------------------------------
    # Function-style Wrapper
    # ---------------------------------------------------------

    def test_function_wrapper_returns_service_response(
        self,
        booking_service,
        future_dates,
        expected_booking_response,
    ):
        """
        Verify the function-style interface that can later
        be exposed to an LLM framework.
        """

        check_in, check_out = future_dates

        booking_service.create_booking.return_value = (
            expected_booking_response
        )

        result = create_booking(
            booking_service=booking_service,
            room_id=4,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            guest_name="John Doe",
            guest_email="john@example.com",
        )

        assert result == expected_booking_response
        booking_service.create_booking.assert_called_once()