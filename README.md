# 🏨 Grand Vista Hotel — AI Booking Agent

An end-to-end hotel room booking assistant built with **LangGraph**, **LangChain**, **Groq**, **FastAPI**, and **Streamlit**. The agent conducts a natural multi-turn conversation with a guest, checks real availability from a PostgreSQL database, and creates confirmed reservations — all within a clean, containerised stack.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Flow](#agent-flow)
- [Project Structure](#project-structure)
- [Room Inventory](#room-inventory)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Configuration](#configuration)

---

## Overview

The agent collects booking requirements over one or more conversation turns:

| Field | Description |
|---|---|
| Check-in date | Must be today or in the future |
| Check-out date | Must be after check-in |
| Bed type | `single` or `double` |
| Breakfast | Included or not |
| Number of guests | ≥ 1 |

Once all five fields are captured, the agent calls an **availability tool** backed by the live database. If rooms are found, the guest selects one, provides their name and email, and the agent creates a **confirmed booking** — returning a booking reference, room details, and total price.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                       Streamlit Frontend                           │
│   Chat UI  ·  Sidebar state display  ·  Booking confirmation       │
└────────────────────────────┬───────────────────────────────────────┘
                             │  HTTP  POST /api/chat
┌────────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                      │
│   POST /api/chat  ·  GET /health                                   │
└────────────────────────────┬───────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│                   HotelBookingAgent  (LangGraph)                   │
│                                                                    │
│  extract_information → validate_requirements → respond             │
│                                      ↑              ↓              │
│                          process_tool_results ← tools (ToolNode)   │
└────────────────────────────┬───────────────────────────────────────┘
                             │  SQLAlchemy
┌────────────────────────────▼───────────────────────────────────────┐
│                   PostgreSQL 16  (port 5432)                       │
│   rooms · reservations · guests · bookings                         │
└────────────────────────────────────────────────────────────────────┘
```

### Two-LLM Design

| LLM | Role | Why |
|---|---|---|
| `extraction_llm` | Structured data extraction via `.with_structured_output()` | Parses dates, bed type, guests, etc. from free-form text into `AgentExtraction` schema |
| `response_llm` | Conversational response + tool calling | Bound with LangChain `@tool` wrappers for `check_availability` and `create_booking`; the model drives tool calls natively |

Both use `openai/gpt-oss-20b` via Groq. The extraction LLM uses temperature 0; the response LLM uses 0.3.

---

## Agent Flow

```
User message
      │
      ▼
extract_information        ← extraction_llm (structured output)
      │                       Parses check-in, check-out, bed type,
      │                       breakfast, guests, room selection, guest info
      ▼
validate_requirements      ← deterministic
      │                       Validates dates, guest count
      ▼
respond                    ← response_llm (tools bound)
      │
      ├──── plain text reply ──────────────────────► END
      │
      └──── tool call ──► tools (ToolNode)
                               │
                               ├── check_availability(...)
                               │       → queries PostgreSQL
                               │       → returns exact matches / alternatives / fully booked
                               │
                               └── create_booking(...)
                                       → creates guest + reservation + booking
                                       → returns booking reference + details
                               │
                               ▼
                    process_tool_results  ← parses ToolMessage JSON
                               │             updates state fields:
                               │             availability, booking_confirmed, etc.
                               ▼
                           respond        ← model reads results, produces text reply
                               │
                               ▼
                              END
```

### State Fields (`BookingState`)

| Field | Type | Description |
|---|---|---|
| `messages` | `list[BaseMessage]` | Full conversation history (append-only) |
| `check_in` | `date \| None` | Extracted check-in date |
| `check_out` | `date \| None` | Extracted check-out date |
| `bed_type` | `str \| None` | `"single"` or `"double"` |
| `breakfast` | `bool \| None` | Breakfast preference |
| `guests` | `int \| None` | Guest count |
| `availability` | `AvailabilityResponse \| None` | Last availability result |
| `availability_checked` | `bool` | Whether availability was fetched for current requirements |
| `selected_room_id` | `int \| None` | DB ID of the room the guest chose |
| `selected_room_no` | `int \| None` | Human-facing room number |
| `guest_name` | `str \| None` | Guest full name |
| `guest_email` | `str \| None` | Guest email |
| `booking` | `BookingResponse \| None` | Completed booking details |
| `booking_confirmed` | `bool` | Whether a booking was successfully created |
| `booking_error` | `str \| None` | Error message if booking failed |
| `requirements_error` | `str \| None` | Validation error (e.g. past check-in date) |

---

## Project Structure

```
Hotel_booking_agent/
├── app/
│   ├── agent_factory.py          # Wires LLMs, DB sessions, tools → agent singleton
│   ├── config.py                 # Pydantic settings (reads .env)
│   ├── main.py                   # FastAPI app + routers
│   │
│   ├── agents/
│   │   ├── dependencies.py       # AgentDependencies dataclass
│   │   ├── graph.py              # LangGraph StateGraph + ToolNode wiring
│   │   ├── lc_tools.py           # LangChain @tool wrappers (check_availability, create_booking)
│   │   ├── nodes.py              # Graph node implementations
│   │   ├── prompts.py            # SYSTEM_PROMPT + EXTRACTION_PROMPT
│   │   ├── schemas.py            # AgentExtraction, BookingRequirements, GuestDetails
│   │   ├── selection.py          # Room selection helpers
│   │   └── state.py              # BookingState TypedDict
│   │
│   ├── api/routes/
│   │   └── chat.py               # POST /api/chat endpoint
│   │
│   ├── database/
│   │   ├── connection.py         # SQLAlchemy engine + SessionLocal
│   │   └── seed.py               # Room + reservation seed data (idempotent)
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── room.py               # Room
│   │   ├── reservation.py        # Reservation
│   │   ├── guest.py              # Guest
│   │   └── booking.py            # Booking
│   │
│   ├── repositories/             # Data access layer
│   │   ├── room_repository.py
│   │   ├── guest_repository.py
│   │   └── booking_repository.py
│   │
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── availability.py       # AvailabilityRequest, AvailabilityResponse, RoomAvailability, AlternativeRoom
│   │   └── booking.py            # BookingCreate, BookingResponse
│   │
│   ├── services/                 # Business logic
│   │   ├── availability_service.py
│   │   ├── alternative_service.py  # Ranked alternatives when no exact match
│   │   └── booking_service.py
│   │
│   └── tools/                    # Service-level tool classes (used by lc_tools wrappers)
│       ├── availability_tool.py
│       └── booking_tool.py
│
├── frontend/
│   └── streamlit_app.py          # Streamlit chat UI + sidebar booking summary
│
├── tests/                        # pytest test suite
│   ├── conftest.py               # Fixtures (test DB, repositories, services)
│   ├── test_availability_service.py
│   ├── test_availability_tool.py
│   ├── test_alternative_service.py
│   ├── test_booking_service.py
│   ├── test_booking_tool.py
│   ├── test_booking_repository.py
│   ├── test_guest_repository.py
│   └── test_room_repository.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

## Room Inventory

Seed data is loaded automatically on first startup (idempotent).

| Room | Type | Bed | Breakfast | Price/Night | Max Guests | Floor |
|------|------|-----|-----------|-------------|------------|-------|
| 101 | Standard | Single | ❌ | ₹2,200 | 1 | 1 |
| 102 | Standard | Single | ✅ | ₹2,600 | 1 | 1 |
| 103 | Standard | Double | ❌ | ₹3,000 | 2 | 1 |
| 104 | Standard | Double | ✅ | ₹3,400 | 2 | 1 |
| 201 | Deluxe | Double | ✅ | ₹4,500 | 2 | 2 |
| 202 | Deluxe | Double | ❌ | ₹4,100 | 2 | 2 |
| 203 | Deluxe | Single | ✅ | ₹3,800 | 1 | 2 |
| 204 | Deluxe | Single | ❌ | ₹3,500 | 1 | 2 |
| 301 | Suite | Double | ✅ | ₹6,500 | 4 | 3 |
| 302 | Suite | Double | ❌ | ₹6,000 | 4 | 3 |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM provider | [Groq](https://groq.com/) — `openai/gpt-oss-20b` |
| Agent framework | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| LLM SDK | [LangChain](https://python.langchain.com/) + `langchain-groq` |
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| Frontend | [Streamlit](https://streamlit.io/) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic v2 |
| Containerisation | Docker + Docker Compose |
| Testing | pytest 8 |

---

## Prerequisites

- **Docker** and **Docker Compose** (recommended)
- A **Groq API key** — get one free at [console.groq.com](https://console.groq.com)

> For local development without Docker you also need Python 3.12 and a running PostgreSQL instance.

---

## Quick Start (Docker)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Hotel_booking_agent.git
cd Hotel_booking_agent
```

### 2. Configure environment variables

```bash
cp .env.example .env   # or edit .env directly
```

Set at minimum:

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-20b
```

### 3. Start all services

```bash
docker compose up --build
```

This starts three containers:

| Container | Service | Port |
|---|---|---|
| `hotel-booking-postgres` | PostgreSQL 16 | 5432 |
| `hotel-booking-app` | FastAPI + Uvicorn | 8000 |
| `hotel-booking-frontend` | Streamlit | 8501 |

The database tables are created and seed data is loaded automatically on first startup.

### 4. Open the app

- **Chat UI** → [http://localhost:8501](http://localhost:8501)
- **API docs** → [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check** → [http://localhost:8000/health](http://localhost:8000/health)

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | — | Groq API key |
| `GROQ_MODEL` | ✅ | — | Groq model name (e.g. `openai/gpt-oss-20b`) |
| `POSTGRES_DB` | ✅ | `hotel_booking` | PostgreSQL database name |
| `POSTGRES_USER` | ✅ | `hotel_user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | ✅ | `hotel_password` | PostgreSQL password |
| `POSTGRES_HOST` | ✅ | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | ✅ | `5432` | PostgreSQL port |
| `DATABASE_URL` | ❌ | built from above | Full SQLAlchemy connection string (overrides individual vars) |
| `TEST_DATABASE_URL` | ❌ | derived | Test database URL (used by pytest) |
| `APP_ENV` | ❌ | `development` | Application environment |

---

## API Reference

### `POST /api/chat`

Send a conversational message to the booking agent.

**Request body:**
```json
{
  "message": "I need a double room with breakfast from September 20 to 23",
  "session_id": "unique-session-uuid"
}
```

**Response:**
```json
{
  "reply": "I found 2 available rooms matching your request...",
  "session_id": "unique-session-uuid"
}
```

> The same `session_id` must be used across all turns of a conversation to maintain context. Each session is isolated via LangGraph's `MemorySaver` checkpointer.

### `GET /health`

Returns `{"status": "healthy"}`.

### `GET /`

Returns `{"status": "ok", "service": "hotel-booking-agent"}`.

---

## Running Tests

Tests run against a separate `hotel_booking_test` PostgreSQL database that is created automatically.

```bash
# From inside the running app container:
docker compose exec app pytest tests/ -v

# Or run a specific test file:
docker compose exec app pytest tests/test_availability_service.py -v
```

The test suite covers:

| Test file | What it covers |
|---|---|
| `test_room_repository.py` | Room queries, filtering |
| `test_guest_repository.py` | Guest creation and lookup |
| `test_booking_repository.py` | Booking creation and retrieval |
| `test_availability_service.py` | Exact match, alternatives, fully booked logic |
| `test_alternative_service.py` | Alternative room ranking and scoring |
| `test_availability_tool.py` | Tool-level availability integration |
| `test_booking_service.py` | End-to-end booking creation, validation, capacity checks |
| `test_booking_tool.py` | Tool-level booking integration |

Each test gets a **fresh, rolled-back database transaction** — no state leaks between tests.

---

## Configuration

### Changing the LLM model

Update `GROQ_MODEL` in `.env`. The model must support **native tool calling** (the agent binds `check_availability` and `create_booking` tools directly to the response LLM).

### Adding rooms

Edit [`app/database/seed.py`](app/database/seed.py) and add entries to the `ROOMS` list. Seed functions are idempotent — they only insert if the table is empty. To re-seed, truncate the `rooms` table first.

### Extending the agent

- **New tool** → add a factory function to `app/agents/lc_tools.py`, include it in `lc_tools` in `agent_factory.py`, and handle its `ToolMessage` result in `process_tool_results` in `nodes.py`.
- **New state field** → add to `BookingState` in `state.py` and update extraction in `nodes.py`.
- **Prompt tuning** → edit `SYSTEM_PROMPT` or `EXTRACTION_PROMPT` in `app/agents/prompts.py`.
