from __future__ import annotations

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.dependencies import AgentDependencies
from app.agents.nodes import HotelBookingNodes
from app.agents.state import BookingState


class HotelBookingAgent:
    def __init__(
        self,
        llm,
        extraction_llm,
        dependencies,
        checkpointer=None,
    ):
        self.nodes = HotelBookingNodes(
            llm=llm,
            extraction_llm=extraction_llm,
            dependencies=dependencies,
        )

        self.checkpointer = (
            checkpointer
            if checkpointer is not None
            else MemorySaver()
        )

        # ToolNode wraps the LangChain @tool callables so LangGraph can
        # automatically execute whatever tool the model chose to call.
        self.tool_node = ToolNode(dependencies.lc_tools)

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
            "respond",
            self.nodes.respond,
        )

        # ToolNode executes whichever tool the model called and appends
        # ToolMessage results to the messages list.
        graph.add_node(
            "tools",
            self.tool_node,
        )

        # After tool execution, parse results back into state fields.
        graph.add_node(
            "process_tool_results",
            self.nodes.process_tool_results,
        )

        # -----------------------------------------------------
        # Edges
        # -----------------------------------------------------

        graph.add_edge(START, "extract_information")
        graph.add_edge("extract_information", "validate_requirements")

        graph.add_conditional_edges(
            "validate_requirements",
            self._route_after_validation,
            {
                "respond": "respond",
            },
        )

        # After respond: if the model emitted tool calls → run tools,
        # otherwise end the turn.
        graph.add_conditional_edges(
            "respond",
            self._route_after_respond,
            {
                "tools": "tools",
                "end": END,
            },
        )

        # Tool execution always flows into result processing.
        graph.add_edge("tools", "process_tool_results")

        # After state is updated from tool results, let the model
        # respond again (it will now produce a conversational reply
        # because tool results are in the messages).
        graph.add_edge("process_tool_results", "respond")

        return graph.compile(
            checkpointer=self.checkpointer,
        )

    # =========================================================
    # Routing
    # =========================================================

    @staticmethod
    def _route_after_validation(
        state: BookingState,
    ) -> Literal["respond"]:
        """
        Always route to respond. The respond node (with tools bound)
        decides on its own whether to call a tool or reply directly.

        Validation errors are passed via state context so the LLM
        can explain them to the guest.
        """
        return "respond"

    @staticmethod
    def _route_after_respond(
        state: BookingState,
    ) -> Literal["tools", "end"]:
        """
        If the last AIMessage has tool_calls, route to the ToolNode.
        Otherwise, the turn is complete.
        """
        messages = state.get("messages", [])

        if not messages:
            return "end"

        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        return "end"

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

    def get_state(self, session_id: str) -> BookingState | None:
        """
        Retrieve the current persisted state for a session.
        """
        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }
        snapshot = self.graph.get_state(config)
        return snapshot.values if snapshot else None


def create_hotel_booking_agent(
    llm,
    dependencies: AgentDependencies,
    extraction_llm,
    checkpointer=None,
) -> HotelBookingAgent:
    """
    Factory for constructing the hotel booking agent.
    """

    return HotelBookingAgent(
        llm=llm,
        extraction_llm=extraction_llm,
        dependencies=dependencies,
        checkpointer=checkpointer,
    )