"""
LangChain tool wrappers for the hotel booking agent.

These @tool decorated functions are bound to the response LLM so that
gpt-oss-20b can call them via the standard tool-calling API instead of
generating invalid free-form tool-call blocks.

The underlying business logic stays in AvailabilityTool / BookingTool —
these are thin wrappers that adapt the interface for LangChain.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Callable

from langchain_core.tools import tool

from app.tools.availability_tool import AvailabilityTool
from app.tools.booking_tool import BookingTool


def make_availability_tool(availability_tool: AvailabilityTool) -> Callable:
    """
    Build a LangChain @tool that calls AvailabilityTool.check_room_availability.

    We use a factory so the tool closes over the service instance that was
    constructed with its own database session in agent_factory.py.
    """

    @tool
    def check_availability(
        check_in: str,
        check_out: str,
        bed_type: str,
        breakfast: bool,
        guests: int,
    ) -> str:
        """
        Check room availability for the requested hotel stay.

        Use this whenever the guest has provided all booking requirements
        (check-in date, check-out date, bed type, breakfast preference,
        and number of guests) and availability has not yet been checked,
        or requirements have changed.

        Args:
            check_in: Check-in date in YYYY-MM-DD format.
            check_out: Check-out date in YYYY-MM-DD format.
            bed_type: Bed type — must be exactly "single" or "double".
            breakfast: True if breakfast should be included, False otherwise.
            guests: Number of guests (must be >= 1).

        Returns:
            JSON string with availability status, matching rooms, and
            any alternatives.
        """
        response = availability_tool.check_room_availability(
            check_in=date.fromisoformat(check_in),
            check_out=date.fromisoformat(check_out),
            bed_type=bed_type,
            breakfast=breakfast,
            guests=guests,
        )
        return response.model_dump_json()

    return check_availability


def make_booking_tool(booking_tool_instance: BookingTool) -> Callable:
    """
    Build a LangChain @tool that calls BookingTool.create_booking.

    Factory pattern keeps the DB session scoped to the injected instance.
    """

    @tool
    def create_booking(
        room_id: int,
        check_in: str,
        check_out: str,
        guests: int,
        guest_name: str,
        guest_email: str,
    ) -> str:
        """
        Create a hotel room booking.

        Only call this after:
        - availability has been checked and a room was selected
        - the guest has confirmed the room selection
        - the guest has provided their full name and email address

        Args:
            room_id: Database ID of the selected room (from availability results).
            check_in: Check-in date in YYYY-MM-DD format.
            check_out: Check-out date in YYYY-MM-DD format.
            guests: Number of guests (must be >= 1).
            guest_name: Full name of the guest.
            guest_email: Valid email address of the guest.

        Returns:
            JSON string with booking reference, guest details, room details,
            stay dates, and total price.
        """
        try:
            response = booking_tool_instance.create_booking(
                room_id=room_id,
                check_in=date.fromisoformat(check_in),
                check_out=date.fromisoformat(check_out),
                guests=guests,
                guest_name=guest_name,
                guest_email=guest_email,
            )
            return response.model_dump_json()
        except ValueError as exc:
            return json.dumps({"error": str(exc)})

    return create_booking
