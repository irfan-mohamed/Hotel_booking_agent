# 🏨 Hotel Booking Agent

A conversational AI assistant that helps guests search for and book hotel rooms at **Grand Vista Hotel**.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│               Streamlit Chat Frontend                     │
│  (Grand Vista Hotel UI — dark premium aesthetic)         │
│  • Booking summary sidebar                               │
│  • Animated chat bubbles (user / assistant)              │
│  • Auto-greeting on first load                           │
└───────────────────────┬──────────────────────────────────┘
                        │ direct Python import
                        ▼
┌──────────────────────────────────────────────────────────┐
│            HotelBookingAgent  (LangGraph)                 │
│                                                          │
│  extract_information                                     │
│       ↓ (LLM: structured output extraction)              │
│  validate_requirements                                   │
│       ↓ (deterministic: date & guest validation)         │
│  check_availability ←── AvailabilityTool                 │
│       ↓ (deterministic: SQL query)                       │
│  create_booking ←────── BookingTool          (optional)  │
│       ↓ (deterministic: transactional write)             │
│  respond                                                 │
│       ↓ (LLM: natural-language response generation)      │
└──────────┬───────────────────────────────────────────────┘
           │ tool calls
           ▼
┌──────────────────────────────────────────────────────────┐
│   AvailabilityService          BookingService            │
│   • find_available_rooms()     • create_booking()        │
│   • find_alternatives()        • re-check availability   │
│   AlternativeService           • generate booking ref    │
│   • score & rank alternatives                            │
└──────────┬───────────────────────────────────────────────┘
           │ SQLAlchemy ORM
           ▼
┌──────────────────────────────────────────────────────────┐
│         RoomRepository / GuestRepository /               │
│         BookingRepository / ReservationRepository        │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│   SQLite  (local dev, auto-created as hotel_booking.db)  │
│   PostgreSQL  (Docker, via docker-compose)               │
└──────────────────────────────────────────────────────────┘
```

### How the LLM and database/tools interact

| Step | Who does the work | What happens |
|------|-------------------|--------------|
| Extract information | **LLM** (Groq `qwen3-32b`) | Parses the user message into structured fields (dates, bed type, breakfast, guests, name, email, room selection). Uses Pydantic structured output — never hallucinates values. |
| Validate requirements | **Deterministic Python** | Checks for past dates, invalid date ranges, guest count < 1. No LLM involved. |
| Check availability | **SQL query** via `RoomRepository` | Finds rooms matching bed type + breakfast + guest capacity with no overlapping confirmed reservation. |
| Find alternatives | **Scoring algorithm** in `AlternativeService` | Scores available rooms on bed type match (50 pts), breakfast match (30 pts), capacity (10 pts). Returns top 2. |
| Create booking | **SQL transaction** via `BookingService` | Re-checks availability, creates/reuses guest, creates reservation + booking atomically. |
| Generate response | **LLM** | Receives the deterministic context (availability results, booking details, errors) and generates a natural-language reply to the guest. |

---

## Room Database

10 rooms seeded automatically across 3 floors:

| Room | Type | Bed | Breakfast | Price/Night | Max Guests |
|------|------|-----|-----------|-------------|------------|
| 101 | Standard | Single | No | ₹2,200 | 1 |
| 102 | Standard | Single | Yes | ₹2,600 | 1 |
| 103 | Standard | Double | No | ₹3,000 | 2 |
| 104 | Standard | Double | Yes | ₹3,400 | 2 |
| 201 | Deluxe | Double | Yes | ₹4,500 | 2 |
| 202 | Deluxe | Double | No | ₹4,100 | 2 |
| 203 | Deluxe | Single | Yes | ₹3,800 | 1 |
| 204 | Deluxe | Single | No | ₹3,500 | 1 |
| 301 | Suite | Double | Yes | ₹6,500 | 4 |
| 302 | Suite | Double | No | ₹6,000 | 4 |

Sample reservations are seeded to demonstrate the "alternatives" flow.

---

## How to Run

### Option 1 — Local (SQLite, no Docker required)

```bash
# 1. Clone / enter the project
cd Hotel_booking_agent

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Groq API key in .env (already configured)
#    GROQ_API_KEY=<your-key>
#    GROQ_MODEL=qwen/qwen3-32b

# 5. Run the Streamlit app
streamlit run frontend/streamlit_app.py
```

The app will automatically:
- Create `hotel_booking.db` (SQLite) on first launch
- Create all tables
- Seed rooms and sample reservations
- Open the chat UI in your browser at http://localhost:8501

### Option 2 — Docker (PostgreSQL)

```bash
docker-compose up --build
```

Access the FastAPI backend at http://localhost:8000/docs  
Access the Streamlit frontend at http://localhost:8501

### Option 3 — FastAPI backend only

```bash
uvicorn app.main:app --reload
# POST /api/chat  { "message": "...", "session_id": "abc" }
```

---

## Project Structure

```
Hotel_booking_agent/
├── app/
│   ├── agent_factory.py        # Wires LLM + DB + services + agent
│   ├── config.py               # Settings (Groq keys, DB URL)
│   ├── main.py                 # FastAPI app
│   ├── agents/
│   │   ├── graph.py            # LangGraph definition & routing
│   │   ├── nodes.py            # Graph nodes (extract / validate / check / respond / book)
│   │   ├── prompts.py          # System & extraction prompts
│   │   ├── schemas.py          # Pydantic extraction schema
│   │   ├── state.py            # BookingState TypedDict
│   │   └── dependencies.py     # AgentDependencies dataclass
│   ├── api/routes/
│   │   └── chat.py             # POST /api/chat
│   ├── database/
│   │   ├── connection.py       # SQLAlchemy engine + session factory
│   │   └── seed.py             # Room & reservation seed data
│   ├── models/                 # SQLAlchemy ORM models
│   ├── repositories/           # Database access layer
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic
│   └── tools/                  # Agent tool wrappers
├── frontend/
│   └── streamlit_app.py        # Full Streamlit chat UI
├── tests/                      # Pytest test suite
├── .env                        # Environment variables
├── requirements.txt
└── docker-compose.yml
```

---

## Conversation Flow

```
Agent greets guest
  ↓
Guest provides check-in / check-out / bed type / breakfast / guests
  ↓ (all 5 fields collected)
Availability check runs automatically (SQL tool call)
  ↓
┌─────────────────────────────────────────────────┐
│ Exact match found?                              │
│   Yes → Present rooms, ask guest to choose      │
│   No  → Suggest 1–2 scored alternatives         │
│   None→ Hotel fully booked — suggest new dates  │
└─────────────────────────────────────────────────┘
  ↓ Guest selects a room
Agent asks for name + email
  ↓ Guest provides details
Booking created (SQL transaction, booking reference generated)
  ↓
Confirmation with booking reference, room details, total price
  (mock email confirmation logged)
```

### Edge cases handled
- **Past / invalid dates**: validated deterministically before any LLM call
- **Guest changes preferences mid-conversation**: previous availability result invalidated, fresh check triggered
- **Price enquiry before committing**: agent presents price/night and total stay when availability is shown
- **Room becomes unavailable between selection and booking**: re-checked at booking time, graceful error reported
- **Fully booked hotel**: `fully_booked` status returned, guest prompted to try different dates
