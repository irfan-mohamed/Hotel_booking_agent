"""
Hotel Booking Agent — Streamlit Chat Frontend
=============================================

Run from the project root:
    streamlit run frontend/streamlit_app.py
"""

from __future__ import annotations

import sys
import os
import uuid

# ---------------------------------------------------------------------------
# Path setup — make "app" importable when running from project root or the
# frontend/ subdirectory.
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

# ---------------------------------------------------------------------------
# Page config (must be the very first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Grand Vista Hotel — Booking Assistant",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — premium dark hotel aesthetic
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* ── Global ────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }

    /* ── Hide default Streamlit chrome ─────────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* ── Hero header ────────────────────────────────────────────────── */
    .hotel-header {
        text-align: center;
        padding: 2rem 1rem 1rem;
        background: linear-gradient(180deg, rgba(139,92,246,0.15) 0%, transparent 100%);
        border-bottom: 1px solid rgba(139,92,246,0.2);
        margin-bottom: 1.5rem;
    }
    .hotel-name {
        font-family: 'Playfair Display', serif;
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #c4b5fd, #8b5cf6, #6d28d9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: 0.02em;
    }
    .hotel-tagline {
        color: #8b949e;
        font-size: 0.9rem;
        font-weight: 300;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-top: 0.3rem;
    }

    /* ── Chat container ─────────────────────────────────────────────── */
    .chat-container {
        max-width: 820px;
        margin: 0 auto;
        padding: 0 1rem;
    }

    /* ── Message bubbles ────────────────────────────────────────────── */
    .msg-wrapper {
        display: flex;
        margin-bottom: 1.2rem;
        animation: fadeSlideIn 0.3s ease-out;
    }
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .msg-wrapper.user { justify-content: flex-end; }
    .msg-wrapper.assistant { justify-content: flex-start; }

    .msg-bubble {
        max-width: 72%;
        padding: 0.85rem 1.1rem;
        border-radius: 18px;
        line-height: 1.6;
        font-size: 0.95rem;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .msg-bubble.user {
        background: linear-gradient(135deg, #6d28d9, #4c1d95);
        color: #f5f0ff;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 15px rgba(109,40,217,0.3);
    }
    .msg-bubble.assistant {
        background: linear-gradient(135deg, #1c2333, #21262d);
        color: #c9d1d9;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(139,92,246,0.2);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    .msg-avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .msg-wrapper.user .msg-avatar {
        margin-left: 0.6rem;
        background: linear-gradient(135deg, #6d28d9, #4c1d95);
        order: 2;
    }
    .msg-wrapper.assistant .msg-avatar {
        margin-right: 0.6rem;
        background: linear-gradient(135deg, #1c2333, #21262d);
        border: 1px solid rgba(139,92,246,0.3);
    }

    /* ── Sidebar ────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid rgba(139,92,246,0.2);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #c9d1d9; }

    .sidebar-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.2rem;
        color: #c4b5fd;
        border-bottom: 1px solid rgba(139,92,246,0.3);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    .info-card {
        background: rgba(139,92,246,0.08);
        border: 1px solid rgba(139,92,246,0.2);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.7rem;
    }
    .info-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8b949e;
        margin-bottom: 0.2rem;
    }
    .info-value {
        font-size: 0.95rem;
        font-weight: 500;
        color: #e6edf3;
    }

    .confirmed-badge {
        display: inline-block;
        background: linear-gradient(135deg, #166534, #15803d);
        color: #bbf7d0;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .booking-ref {
        font-family: 'Courier New', monospace;
        font-size: 1.1rem;
        font-weight: 700;
        color: #a78bfa;
        letter-spacing: 0.1em;
    }

    /* ── Input area ─────────────────────────────────────────────────── */
    .stChatInputContainer {
        background: rgba(22,27,34,0.95) !important;
        border-top: 1px solid rgba(139,92,246,0.2) !important;
        padding: 0.75rem 1rem !important;
    }
    .stChatInput textarea {
        background: rgba(13,17,23,0.8) !important;
        border: 1px solid rgba(139,92,246,0.3) !important;
        border-radius: 12px !important;
        color: #e6edf3 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stChatInput textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 2px rgba(139,92,246,0.2) !important;
    }

    /* ── Spinner ────────────────────────────────────────────────────── */
    .thinking-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #8b949e;
        font-size: 0.88rem;
        padding: 0.5rem 0 0.5rem 44px;
        font-style: italic;
    }
    .dot-pulse {
        display: flex;
        gap: 4px;
    }
    .dot-pulse span {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #8b5cf6;
        animation: dotPulse 1.4s ease-in-out infinite;
    }
    .dot-pulse span:nth-child(2) { animation-delay: 0.2s; }
    .dot-pulse span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dotPulse {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40%            { transform: scale(1.0); opacity: 1.0; }
    }

    /* ── Divider ────────────────────────────────────────────────────── */
    hr { border-color: rgba(139,92,246,0.15) !important; }

    /* ── New session button ─────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #6d28d9, #4c1d95) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_session() -> None:
    """Initialise all session state keys if not already set."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "chat_history" not in st.session_state:
        # Each entry: {"role": "user"|"assistant", "content": str}
        st.session_state.chat_history = []
    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "agent_error" not in st.session_state:
        st.session_state.agent_error = None


_init_session()

# ---------------------------------------------------------------------------
# Lazy-load the agent (only once per Streamlit session)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _load_agent():
    """Load the booking agent — cached across Streamlit reruns."""
    from app.agent_factory import get_agent  # noqa: PLC0415
    return get_agent()


def get_agent_safe():
    """Return the agent or an error string."""
    try:
        return _load_agent(), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


# ---------------------------------------------------------------------------
# Helper — call agent and return reply + updated booking state
# ---------------------------------------------------------------------------

def send_message(message: str) -> str:
    """Send a message to the agent and return the assistant reply."""
    agent, err = get_agent_safe()
    if err:
        return f"⚠️ Could not load agent: {err}"

    try:
        state = agent.invoke(
            message=message,
            session_id=st.session_state.session_id,
        )
        messages = state.get("messages", [])
        return messages[-1].content if messages else "..."
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Error: {exc}"


def get_current_booking_state() -> dict | None:
    """Retrieve the current agent state for the active session."""
    agent, _ = get_agent_safe()
    if agent is None:
        return None
    try:
        return agent.get_state(st.session_state.session_id)
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Sidebar — booking summary
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">🏨 Grand Vista Hotel</div>',
            unsafe_allow_html=True,
        )

        state = get_current_booking_state() or {}

        # ── Booking confirmed banner ──────────────────────────────────
        booking = state.get("booking")
        if booking and state.get("booking_confirmed"):
            ref = booking.booking_reference
            st.markdown(
                f'<div class="confirmed-badge">✅ BOOKING CONFIRMED</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="booking-ref">{ref}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("---")

        # ── Search preferences ────────────────────────────────────────
        st.markdown("**Search Preferences**")

        def _card(label: str, value) -> None:
            if value is not None and value != "":
                st.markdown(
                    f'<div class="info-card">'
                    f'<div class="info-label">{label}</div>'
                    f'<div class="info-value">{value}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

        _card("Check-in", state.get("check_in"))
        _card("Check-out", state.get("check_out"))
        _card("Bed type", (state.get("bed_type") or "").capitalize() or None)

        breakfast = state.get("breakfast")
        if breakfast is not None:
            _card("Breakfast", "✅ Included" if breakfast else "❌ Not included")

        _card("Guests", state.get("guests"))

        # ── Room selection ────────────────────────────────────────────
        room_no = state.get("selected_room_no")
        if room_no:
            st.markdown("---")
            st.markdown("**Selected Room**")
            _card("Room No.", room_no)

        # ── Guest details ─────────────────────────────────────────────
        name = state.get("guest_name")
        email = state.get("guest_email")
        if name or email:
            st.markdown("---")
            st.markdown("**Guest Details**")
            _card("Name", name)
            _card("Email", email)

        # ── Booking details ───────────────────────────────────────────
        if booking:
            st.markdown("---")
            st.markdown("**Booking Details**")
            # BookingResponse is a Pydantic model — access fields directly.
            _card("Room", f"#{booking.room_no} — {booking.room_type}")
            _card("Bed", (booking.bed_type or "").capitalize())
            _card("Breakfast", "✅ Yes" if booking.breakfast else "❌ No")
            if booking.nights and booking.price_per_night:
                _card("Stay", f"{booking.nights} night{'s' if booking.nights != 1 else ''}")
                _card("Price / night", f"₹{float(booking.price_per_night):,.0f}")
            if booking.total_price:
                _card("Total", f"₹{float(booking.total_price):,.0f}")
            _card("Status", (booking.status or "").upper())

        # ── Session info / new session ────────────────────────────────
        st.markdown("---")
        st.markdown(
            f'<div style="color:#8b949e;font-size:0.75rem;margin-bottom:0.5rem;">'
            f'Session: <code>{st.session_state.session_id[:8]}…</code>'
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 New Conversation", key="new_session_btn"):
            # Clear session and rerun
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ---------------------------------------------------------------------------
# Main layout — header + chat
# ---------------------------------------------------------------------------

def render_header() -> None:
    st.markdown(
        """
        <div class="hotel-header">
            <div class="hotel-name">✦ Grand Vista Hotel ✦</div>
            <div class="hotel-tagline">AI-Powered Room Booking Assistant</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history() -> None:
    """Render all past messages."""
    for msg in st.session_state.chat_history:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            st.markdown(
                f"""
                <div class="msg-wrapper user">
                    <div class="msg-bubble user">{content}</div>
                    <div class="msg-avatar">👤</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="msg-wrapper assistant">
                    <div class="msg-avatar">🏨</div>
                    <div class="msg-bubble assistant">{content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_thinking_indicator() -> None:
    st.markdown(
        """
        <div class="thinking-indicator">
            <div class="dot-pulse">
                <span></span><span></span><span></span>
            </div>
            Grand Vista is thinking…
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------

render_sidebar()
render_header()

# ── Greeting on first load ─────────────────────────────────────────────────
if not st.session_state.greeted:
    with st.spinner("Connecting to Grand Vista Hotel…"):
        greeting = send_message("Hello")
    st.session_state.chat_history.append(
        {"role": "assistant", "content": greeting}
    )
    st.session_state.greeted = True

# ── Render message history ─────────────────────────────────────────────────
render_chat_history()

# ── Chat input ─────────────────────────────────────────────────────────────
user_input = st.chat_input(
    "Type your message here…",
    key="chat_input",
)

if user_input and user_input.strip():
    # 1. Append user message to history and display it immediately
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input.strip()}
    )

    # 2. Show the updated history (including the new user message)
    #    then show the thinking indicator while waiting
    render_chat_history()
    thinking_placeholder = st.empty()
    with thinking_placeholder:
        render_thinking_indicator()

    # 3. Invoke the agent
    reply = send_message(user_input.strip())

    # 4. Clear indicator, append assistant reply, rerun to refresh sidebar
    thinking_placeholder.empty()
    st.session_state.chat_history.append(
        {"role": "assistant", "content": reply}
    )

    st.rerun()
