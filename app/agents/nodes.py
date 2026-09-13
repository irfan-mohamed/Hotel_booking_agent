from __future__ import annotations

from datetime import date

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langgraph.graph import END

from app.agents.dependencies import AgentDependencies
from app.agents.prompts import EXTRACTION_PROMPT, SYSTEM_PROMPT
from app.agents.schemas import AgentExtraction
from app.agents.state import BookingState


class HotelBookingNodes:
    """
    Nodes used by the hotel booking LangGraph.

    LLM responsibilities:
        - understand the user's message
        - extract structured information
        - generate conversational responses

    Deterministic responsibilities:
        - deciding whether required fields exist
        - availability
        - booking
        - validation
    """

    def __init__(
        self,
        llm,
        dependencies: AgentDependencies,
    ):
        self.llm = llm
        self.dependencies = dependencies

        self.extraction_llm = llm.with_structured_output(
            AgentExtraction
        )

    # =========================================================
    # Extraction
    # =========================================================

    def extract_information(
        self,
        state: BookingState,
    ) -> dict:
        """
        Extract booking information from the latest user message.

        The LLM does not replace existing state. It only provides
        possible updates.
        """

        messages = state.get("messages", [])

        if not messages:
            return {}

        latest_user_message = None

        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                latest_user_message = message
                break

        if latest_user_message is None:
            return {}

        extraction_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    EXTRACTION_PROMPT,
                ),
                (
                    "human",
                    "{message}",
                ),
            ]
        )

        chain = extraction_prompt | self.extraction_llm

        extraction: AgentExtraction = chain.invoke(
            {
                "message": latest_user_message.content,
            }
        )

        updates = {}

        fields = [
            "check_in",
            "check_out",
            "bed_type",
            "breakfast",
            "guests",
            "guest_name",
            "guest_email",
        ]

        for field in fields:
            value = getattr(extraction, field)

            if value is not None:
                updates[field] = value

        if extraction.room_id is not None:
            updates["selected_room_id"] = extraction.room_id

        if extraction.room_no is not None:
            updates["selected_room_no"] = extraction.room_no

        # Any requirement change invalidates the previous
        # availability result.
        requirement_fields = {
            "check_in",
            "check_out",
            "bed_type",
            "breakfast",
            "guests",
        }

        if requirement_fields.intersection(updates):
            updates["availability_checked"] = False
            updates["availability"] = None

            # A changed search means the previous room selection
            # is no longer valid.
            updates["selected_room_id"] = None
            updates["selected_room_no"] = None

        return updates

    # =========================================================
    # Requirement validation
    # =========================================================

    def validate_requirements(
        self,
        state: BookingState,
    ) -> dict:
        """
        Deterministically validate the booking requirements.

        The LLM is not used for this decision.
        """

        check_in = state.get("check_in")
        check_out = state.get("check_out")
        bed_type = state.get("bed_type")
        breakfast = state.get("breakfast")
        guests = state.get("guests")

        errors: list[str] = []

        if check_in is not None:
            if check_in < date.today():
                errors.append(
                    "Check-in date cannot be in the past."
                )

        if check_in is not None and check_out is not None:
            if check_out <= check_in:
                errors.append(
                    "Check-out date must be after check-in date."
                )

        if guests is not None and guests < 1:
            errors.append(
                "Number of guests must be at least 1."
            )

        if errors:
            return {
                "requirements_error": " ".join(errors),
                "availability_checked": False,
                "availability": None,
            }

        return {
            "requirements_error": None,
        }

    # =========================================================
    # Availability
    # =========================================================

    def check_availability(
        self,
        state: BookingState,
    ) -> dict:
        """
        Call the deterministic availability tool.

        This node is only reached when all required booking
        requirements are available and valid.
        """

        response = (
            self.dependencies.availability_tool
            .check_room_availability(
                check_in=state["check_in"],
                check_out=state["check_out"],
                bed_type=state["bed_type"],
                breakfast=state["breakfast"],
                guests=state["guests"],
            )
        )

        return {
            "availability": response,
            "availability_checked": True,
            "requirements_error": None,
        }

    # =========================================================
    # Response generation
    # =========================================================

    def respond(
        self,
        state: BookingState,
    ) -> dict:
        """
        Generate the next conversational response.

        Tool results and state are supplied to the LLM.
        """

        availability = state.get("availability")

        context = {
            "check_in": state.get("check_in"),
            "check_out": state.get("check_out"),
            "bed_type": state.get("bed_type"),
            "breakfast": state.get("breakfast"),
            "guests": state.get("guests"),
            "selected_room_id": state.get("selected_room_id"),
            "selected_room_no": state.get("selected_room_no"),
            "guest_name": state.get("guest_name"),
            "guest_email": state.get("guest_email"),
            "availability": (
                availability.model_dump(mode="json")
                if availability
                else None
            ),
            "booking": (
                state["booking"].model_dump(mode="json")
                if state.get("booking")
                else None
            ),
            "requirements_error": state.get(
                "requirements_error"
            ),
            "booking_error": state.get("booking_error"),
        }

        response_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    SYSTEM_PROMPT,
                ),
                (
                    "placeholder",
                    "{messages}",
                ),
                (
                    "system",
                    """
Current deterministic booking state:

{context}
""",
                ),
            ]
        )

        chain: Runnable = response_prompt | self.llm

        response = chain.invoke(
            {
                "messages": state.get("messages", []),
                "context": context,
            }
        )

        return {
            "messages": [
                AIMessage(
                    content=response.content,
                )
            ]
        }

    # =========================================================
    # Booking
    # =========================================================

    def create_booking(
        self,
        state: BookingState,
    ) -> dict:
        """
        Create the booking using the deterministic booking tool.
        """

        try:
            response = (
                self.dependencies.booking_tool
                .create_booking(
                    room_id=state["selected_room_id"],
                    check_in=state["check_in"],
                    check_out=state["check_out"],
                    guests=state["guests"],
                    guest_name=state["guest_name"],
                    guest_email=state["guest_email"],
                )
            )

            return {
                "booking": response,
                "booking_error": None,
            }

        except ValueError as exc:
            return {
                "booking": None,
                "booking_error": str(exc),
            }