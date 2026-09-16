from __future__ import annotations

import json
from datetime import date

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.dependencies import AgentDependencies
from app.agents.prompts import EXTRACTION_PROMPT, SYSTEM_PROMPT
from app.agents.schemas import AgentExtraction
from app.agents.state import BookingState
from app.schemas.availability import AvailabilityResponse
from app.schemas.booking import BookingResponse


class HotelBookingNodes:
    """
    Nodes used by the hotel booking LangGraph.

    LLM responsibilities:
        - extract structured booking information from each user message
        - generate conversational responses AND call availability /
          booking tools when needed (tool-calling model)

    Deterministic responsibilities:
        - validate booking requirements
        - update state from tool call results
        - routing decisions
    """

    def __init__(
        self,
        llm,
        extraction_llm,
        dependencies: AgentDependencies,
    ):
        self.extraction_llm = extraction_llm.with_structured_output(
            AgentExtraction,
        )
        self.dependencies = dependencies

        # Bind the LangChain tools to the response LLM so gpt-oss-20b
        # can call them properly via the tool-calling API.
        if dependencies.lc_tools:
            self.llm = llm.bind_tools(dependencies.lc_tools)
        else:
            self.llm = llm

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
                    "system",
                    "Today's date is {today}.",
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
                "today": date.today().isoformat(),
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

            # If requirements change, the booking is no longer confirmed.
            updates["booking_confirmed"] = False
            updates["booking"] = None

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
    # Tool result processing
    # =========================================================

    def process_tool_results(
        self,
        state: BookingState,
    ) -> dict:
        """
        After the ToolNode executes tool calls, parse the ToolMessage
        results and update structured state fields.

        This node runs after every ToolNode execution so routing logic
        downstream can still use state fields (availability_checked,
        booking_confirmed, etc.) rather than parsing raw messages.
        """

        messages = state.get("messages", [])
        updates: dict = {}

        # Walk backwards through messages to find unprocessed ToolMessages.
        for msg in reversed(messages):
            if not isinstance(msg, ToolMessage):
                break  # stop at the first non-ToolMessage

            try:
                payload = json.loads(msg.content)
            except (json.JSONDecodeError, TypeError):
                continue

            # ---- availability result --------------------------------
            if msg.name == "check_availability":
                try:
                    availability = AvailabilityResponse.model_validate(payload)
                    updates["availability"] = availability
                    updates["availability_checked"] = True
                    updates["requirements_error"] = None
                except Exception:
                    pass

            # ---- booking result ------------------------------------
            elif msg.name == "create_booking":
                if "error" in payload:
                    updates["booking"] = None
                    updates["booking_confirmed"] = False
                    updates["booking_error"] = payload["error"]
                else:
                    try:
                        booking = BookingResponse.model_validate(payload)
                        updates["booking"] = booking
                        updates["booking_confirmed"] = True
                        updates["booking_error"] = None
                    except Exception:
                        pass

        return updates

    # =========================================================
    # Response generation
    # =========================================================

    def respond(
        self,
        state: BookingState,
    ) -> dict:
        """
        Generate the next conversational response.

        The response LLM has tools bound to it. If the model decides a
        tool call is needed, it emits an AIMessage with tool_calls — the
        graph then routes to the ToolNode. If it produces plain text,
        the graph ends the turn.
        """

        availability = state.get("availability")

        context = {
            "check_in": str(state.get("check_in")) if state.get("check_in") else None,
            "check_out": str(state.get("check_out")) if state.get("check_out") else None,
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
            "booking_confirmed": state.get("booking_confirmed", False),
            "requirements_error": state.get("requirements_error"),
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
Current booking state:

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
            "messages": [response],
        }