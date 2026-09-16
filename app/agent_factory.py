"""
Agent factory.

This module is the single place that wires together:
    - Groq LLM (from config)
    - SQLAlchemy database session
    - Repositories → Services → Tools → AgentDependencies
    - HotelBookingAgent

Both the Streamlit frontend and FastAPI backend import from here.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver

from app.agents.dependencies import AgentDependencies
from app.agents.graph import HotelBookingAgent, create_hotel_booking_agent
from app.agents.lc_tools import make_availability_tool, make_booking_tool
from app.config import settings
from app.database.connection import Base, SessionLocal, engine
from app.repositories.booking_repository import BookingRepository
from app.repositories.guest_repository import GuestRepository
from app.repositories.room_repository import RoomRepository
from app.services.alternative_service import AlternativeService
from app.services.availability_service import AvailabilityService
from app.services.booking_service import BookingService
from app.tools.availability_tool import AvailabilityTool
from app.tools.booking_tool import BookingTool


def ensure_database_ready() -> None:
    """
    Create all tables and seed initial data if the database is empty.

    Safe to call multiple times — the seed functions are idempotent
    (they check for existing data before inserting).
    """
    # Import models so their metadata is registered before create_all.
    from app.models import Booking, Guest, Reservation, Room  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Run seed data
    from app.database.seed import seed_rooms, seed_reservations  # noqa: PLC0415

    with SessionLocal() as session:
        seed_rooms(session)
        seed_reservations(session)


@lru_cache(maxsize=1)
def get_agent() -> HotelBookingAgent:
    """
    Build and return the singleton HotelBookingAgent.

    The agent uses an in-memory LangGraph MemorySaver checkpointer,
    so multiple Streamlit sessions are isolated by their thread_id
    (session_id).

    Cached via lru_cache — the LLM, database engine, and LangGraph
    graph are constructed only once per process.
    """

    ensure_database_ready()

    # ----------------------------------------------------------------
    # LLM
    # ----------------------------------------------------------------
    response_llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.3,
        reasoning_effort="low",
        max_tokens=1024,
    )

    extraction_llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0,
        reasoning_effort="low",
        max_tokens=200,
    )
    # ----------------------------------------------------------------
    # Shared database sessions for tool instances.
    # Each tool keeps its own session for thread isolation.
    # ----------------------------------------------------------------
    avail_db = SessionLocal()
    booking_db = SessionLocal()

    # ---- Availability -----------------------------------------------
    avail_room_repo = RoomRepository(avail_db)
    alt_service = AlternativeService(room_repository=avail_room_repo)
    avail_service = AvailabilityService(
        room_repository=avail_room_repo,
        alternative_service=alt_service,
    )
    avail_tool = AvailabilityTool(availability_service=avail_service)

    # ---- Booking ----------------------------------------------------
    booking_room_repo = RoomRepository(booking_db)
    guest_repo = GuestRepository(booking_db)
    booking_repo = BookingRepository(booking_db)
    booking_service = BookingService(
        db=booking_db,
        room_repository=booking_room_repo,
        guest_repository=guest_repo,
        booking_repository=booking_repo,
    )
    booking_tool = BookingTool(booking_service=booking_service)

    # ----------------------------------------------------------------
    # LangChain @tool wrappers
    # These are bound to response_llm so gpt-oss-20b can call them
    # via the standard tool-calling API.
    # ----------------------------------------------------------------
    lc_availability_tool = make_availability_tool(avail_tool)
    lc_booking_tool = make_booking_tool(booking_tool)
    lc_tools = [lc_availability_tool, lc_booking_tool]

    # ----------------------------------------------------------------
    # Assemble agent
    # ----------------------------------------------------------------
    dependencies = AgentDependencies(
        availability_tool=avail_tool,
        booking_tool=booking_tool,
        lc_tools=lc_tools,
    )

    checkpointer = MemorySaver()

    agent = create_hotel_booking_agent(
        llm=response_llm,
        extraction_llm=extraction_llm,
        dependencies=dependencies,
        checkpointer=checkpointer,
    )

    return agent
