"""
Quick smoke-test for Langfuse observability.

Run from the project root:
    .venv\\Scripts\\python test_langfuse.py

What it does:
  1. Initialises the Langfuse client from .env
  2. Creates a trace + two child spans (simulated LLM + tool call)
  3. Flushes everything to Langfuse
  4. Prints the direct URL to the trace on us.cloud.langfuse.com
"""

import sys
import os
import time

# Make sure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

print("=" * 60)
print("Langfuse Observability — Connection Test")
print("=" * 60)
print(f"  HOST       : {settings.langfuse_base_url}")
print(f"  PUBLIC KEY : {settings.langfuse_public_key[:12]}...")
print(f"  SECRET KEY : {settings.langfuse_secret_key[:12]}...")
print()

# ------------------------------------------------------------------
# 1. Build the client directly (bypasses the lazy singleton)
# ------------------------------------------------------------------
try:
    from langfuse import Langfuse

    lf = Langfuse(
        secret_key=settings.langfuse_secret_key,
        public_key=settings.langfuse_public_key,
        host=settings.langfuse_base_url,
    )
    print("✅  Langfuse client created successfully.")
except Exception as exc:
    print(f"❌  Failed to create Langfuse client: {exc}")
    sys.exit(1)

# ------------------------------------------------------------------
# 2. Create a root trace
# ------------------------------------------------------------------
trace = lf.trace(
    name="hotel-booking-agent-turn",
    input="I need a double room from Nov 10 to Nov 15 for 2 guests",
    session_id="smoke-test-session",
    tags=["smoke-test", "hotel-booking"],
    metadata={"test": True},
)
print(f"✅  Trace created  → id: {trace.id}")

# ------------------------------------------------------------------
# 3. Simulate extraction LLM span
# ------------------------------------------------------------------
t0 = time.perf_counter()
time.sleep(0.05)   # pretend 50ms LLM call
gen = trace.generation(
    name="extract_information",
    model="openai/gpt-oss-20b",
    input="I need a double room from Nov 10 to Nov 15 for 2 guests",
    output='{"check_in": "2025-11-10", "check_out": "2025-11-15", "bed_type": "double", "guests": 2}',
    usage={
        "input": 142,
        "output": 38,
        "total": 180,
        "unit": "TOKENS",
    },
    metadata={"latency_ms": round((time.perf_counter() - t0) * 1000, 2)},
)
gen.end()
print("✅  extraction LLM generation span sent.")

# ------------------------------------------------------------------
# 4. Simulate tool span — check_availability
# ------------------------------------------------------------------
t1 = time.perf_counter()
time.sleep(0.03)
tool_span = trace.span(
    name="tool:check_availability",
    input={"check_in": "2025-11-10", "check_out": "2025-11-15", "bed_type": "double", "guests": 2},
    output='{"available": true, "rooms": [{"room_id": 3, "room_no": 101}]}',
    metadata={"latency_ms": round((time.perf_counter() - t1) * 1000, 2), "status": "success"},
)
tool_span.end()
print("✅  tool:check_availability span sent.")

# ------------------------------------------------------------------
# 5. Simulate respond LLM span
# ------------------------------------------------------------------
t2 = time.perf_counter()
time.sleep(0.07)
gen2 = trace.generation(
    name="respond",
    model="openai/gpt-oss-20b",
    input={"messages_count": 3, "context_keys": ["check_in", "check_out", "availability"]},
    output="Great news! Room 101 (Double) is available from Nov 10–15 for 2 guests. Shall I book it?",
    usage={
        "input": 280,
        "output": 52,
        "total": 332,
        "unit": "TOKENS",
    },
    metadata={"latency_ms": round((time.perf_counter() - t2) * 1000, 2)},
)
gen2.end()
print("✅  respond LLM generation span sent.")

# ------------------------------------------------------------------
# 6. Close root trace with final metadata
# ------------------------------------------------------------------
trace.update(
    output="Great news! Room 101 (Double) is available from Nov 10–15 for 2 guests. Shall I book it?",
    metadata={
        "total_latency_ms": 160.0,
        "total_prompt_tokens": 422,
        "total_completion_tokens": 90,
        "total_tokens": 512,
        "tool_calls_summary": [
            {"tool": "check_availability", "latency_ms": 30.1, "result_preview": "available=True"}
        ],
    },
)
print("✅  Root trace updated with aggregated metrics.")

# ------------------------------------------------------------------
# 7. Flush
# ------------------------------------------------------------------
lf.flush()
print("✅  Flushed to Langfuse.\n")

print("=" * 60)
print("🎯  Check your Langfuse dashboard now:")
print(f"    {settings.langfuse_base_url}")
print()
print(f"    Direct trace URL (if supported by your plan):")
print(f"    {settings.langfuse_base_url}/trace/{trace.id}")
print("=" * 60)
