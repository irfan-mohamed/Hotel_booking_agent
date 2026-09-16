"""
Chat API route.

POST /api/chat
    Accepts a user message and session_id, invokes the hotel booking
    agent, and returns the latest assistant response.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent_factory import get_agent

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the hotel booking agent",
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Process one conversational turn with the hotel booking agent.

    - **message**: The guest's latest message.
    - **session_id**: A unique identifier for the conversation session.
      The same session_id must be used across turns to maintain context.
    """

    agent = get_agent()

    state = agent.invoke(
        message=request.message,
        session_id=request.session_id,
    )

    # The last message in the state is always the assistant's reply.
    messages = state.get("messages", [])
    reply = messages[-1].content if messages else ""

    return ChatResponse(
        reply=reply,
        session_id=request.session_id,
    )
