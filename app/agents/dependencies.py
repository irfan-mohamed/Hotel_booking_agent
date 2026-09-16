from dataclasses import dataclass, field
from typing import Any

from app.tools.availability_tool import AvailabilityTool
from app.tools.booking_tool import BookingTool


@dataclass(frozen=True)
class AgentDependencies:
    """
    Dependencies required by the hotel booking agent.

    Database/service construction happens outside the agent.

    lc_tools contains the LangChain @tool callables bound to the
    response LLM, enabling gpt-oss-20b to call them via the standard
    tool-calling API.
    """

    availability_tool: AvailabilityTool
    booking_tool: BookingTool
    lc_tools: list[Any] = field(default_factory=list)