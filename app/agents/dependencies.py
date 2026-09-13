from dataclasses import dataclass

from app.tools.availability_tool import AvailabilityTool
from app.tools.booking_tool import BookingTool


@dataclass(frozen=True)
class AgentDependencies:
    """
    Dependencies required by the hotel booking agent.

    Database/service construction happens outside the agent.
    """

    availability_tool: AvailabilityTool
    booking_tool: BookingTool