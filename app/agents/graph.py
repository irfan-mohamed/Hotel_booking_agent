from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.dependencies import AgentDependencies
from app.agents.nodes import HotelBookingNodes
from app.agents.state import BookingState


class HotelBookingAgent:
    """
    Stateful conversational hotel booking agent.
    """

    def __init__(
        self,
        llm,
        dependencies: AgentDependencies,
        checkpointer=None,
    ):
        self.nodes = HotelBookingNodes(
            llm=llm,
            dependencies=dependencies,
        )

        self.checkpointer = (
            checkpointer
            if checkpointer is not None
            else MemorySaver()
        )

        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(BookingState)

        # -----------------------------------------------------
        # Nodes
        # -----------------------------------------------------

        graph.add_node(
            "extract_information",
            self.nodes.extract_information,
        )

        graph.add_node(
            "validate_requirements",
            self.nodes.validate_requirements,
        )

        graph.add_node(
            "check_availability",
            self.nodes.check_availability,
        )

        graph.add_node(
            "respond",
            self.nodes.respond,
        )

        # -----------------------------------------------------
        # Edges
        # -----------------------------------------------------

        graph.add_edge(
            START,
            "extract_information",
        )

        graph.add_edge(
            "extract_information",
            "validate_requirements",
        )

        graph.add_conditional_edges(
            "validate_requirements",
            self._route_after_validation,
            {
                "respond": "respond",
                "availability": "check_availability",
            },
        )

        graph.add_edge(
            "check_availability",
            "respond",
        )

        graph.add_edge(
            "respond",
            END,
        )

        return graph.compile(
            checkpointer=self.checkpointer,
        )

    # =========================================================
    # Routing
    # =========================================================

    @staticmethod
    def _route_after_validation(
        state: BookingState,
    ) -> Literal[
        "respond",
        "availability",
    ]:
        """
        Decide whether the availability tool can be called.

        This decision is deterministic.
        """

        if state.get("requirements_error"):
            return "respond"

        required_fields = [
            "check_in",
            "check_out",
            "bed_type",
            "breakfast",
            "guests",
        ]

        requirements_complete = all(
            state.get(field) is not None
            for field in required_fields
        )

        if not requirements_complete:
            return "respond"

        if state.get("availability_checked"):
            return "respond"

        return "availability"

    # =========================================================
    # Public interface
    # =========================================================

    def invoke(
        self,
        message: str,
        session_id: str,
    ) -> BookingState:
        """
        Process one user message.

        session_id identifies the conversation thread.
        """

        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }

        result = self.graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=message,
                    )
                ],
            },
            config=config,
        )

        return result


def create_hotel_booking_agent(
    llm,
    dependencies: AgentDependencies,
    checkpointer=None,
) -> HotelBookingAgent:
    """
    Factory for constructing the hotel booking agent.
    """

    return HotelBookingAgent(
        llm=llm,
        dependencies=dependencies,
        checkpointer=checkpointer,
    )