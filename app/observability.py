"""
Observability layer — Langfuse tracing for the Hotel Booking Agent.

This module provides:
  - A singleton Langfuse client (initialised from settings).
  - A context-variable that carries the *active trace* through a single
    agent invocation so every node/tool span is nested under it.
  - Helper context-managers used by nodes and the graph to create spans
    with automatic latency, token counting, and status tracking.

Usage
-----
1.  At the start of every chat turn, call ``start_trace(...)`` which
    returns a ``TraceContext`` that owns the root Langfuse trace.
2.  Inside each node, call ``llm_generation_span(...)`` to create a
    child generation span.
3.  When the turn is finished, call ``TraceContext.finish()`` to flush
    final metadata (total latency, turn-level token totals).
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy Langfuse client
# ---------------------------------------------------------------------------

_langfuse_client = None


def get_langfuse():
    """Return the singleton Langfuse client, creating it on first call."""
    global _langfuse_client  # noqa: PLW0603
    if _langfuse_client is not None:
        return _langfuse_client

    try:
        from app.config import settings  # local import avoids circular imports
        from langfuse import Langfuse  # noqa: PLC0415

        _langfuse_client = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_base_url,
        )
        logger.info("Langfuse observability client initialised.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Langfuse not available — observability disabled. Reason: %s", exc
        )
        _langfuse_client = _NoopLangfuse()

    return _langfuse_client


# ---------------------------------------------------------------------------
# No-op fallback (when Langfuse is not configured / unreachable)
# ---------------------------------------------------------------------------


class _NoopSpan:
    """Drop-in replacement for a Langfuse generation/span when tracing is off."""

    def update(self, **_kwargs) -> None:
        pass

    def end(self, **_kwargs) -> None:
        pass

    def score(self, **_kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        pass


class _NoopTrace(_NoopSpan):
    def span(self, **_kwargs) -> _NoopSpan:
        return _NoopSpan()

    def generation(self, **_kwargs) -> _NoopSpan:
        return _NoopSpan()

    def flush(self) -> None:
        pass


class _NoopLangfuse:
    def trace(self, **_kwargs) -> _NoopTrace:
        return _NoopTrace()

    def flush(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Context variable — carries the active trace across the call stack
# ---------------------------------------------------------------------------

_active_trace: ContextVar[Any] = ContextVar("_active_trace", default=None)
_active_trace_ctx: ContextVar[Any] = ContextVar("_active_trace_ctx", default=None)


# ---------------------------------------------------------------------------
# TraceContext — owns one full agent turn
# ---------------------------------------------------------------------------


@dataclass
class TraceContext:
    """
    Wraps a single Langfuse trace that corresponds to one user -> agent turn.

    Accumulates token counts from all child generations and records final
    totals + total wall-clock latency when ``finish()`` is called.
    """

    trace: Any          # langfuse.Trace or _NoopTrace
    session_id: str
    user_query: str
    _start: float = field(default_factory=time.perf_counter, init=False)
    _total_prompt_tokens: int = field(default=0, init=False)
    _total_completion_tokens: int = field(default=0, init=False)
    _tool_calls: list = field(default_factory=list, init=False)

    # ------------------------------------------------------------------
    # Token / tool-call accumulation
    # ------------------------------------------------------------------

    def add_usage(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens

    def add_tool_call(self, tool_name: str, latency_ms: float, result_preview: str) -> None:
        self._tool_calls.append(
            {
                "tool": tool_name,
                "latency_ms": round(latency_ms, 2),
                "result_preview": result_preview[:300],
            }
        )

    # ------------------------------------------------------------------
    # Finalise
    # ------------------------------------------------------------------

    def finish(self, output: str = "") -> None:
        """
        Stamp the trace with aggregated metrics and flush to Langfuse.
        Call this after graph.invoke() returns.
        """
        total_latency_ms = (time.perf_counter() - self._start) * 1_000

        try:
            self.trace.update(
                output=output,
                metadata={
                    "total_latency_ms": round(total_latency_ms, 2),
                    "total_prompt_tokens": self._total_prompt_tokens,
                    "total_completion_tokens": self._total_completion_tokens,
                    "total_tokens": (
                        self._total_prompt_tokens + self._total_completion_tokens
                    ),
                    "tool_calls_summary": self._tool_calls,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse trace.update error: %s", exc)

        try:
            get_langfuse().flush()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse flush error: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_trace(
    user_query: str,
    session_id: str,
    tags: list[str] | None = None,
) -> TraceContext:
    """
    Create a new Langfuse trace for one agent turn.

    Returns a ``TraceContext``; callers **must** call ``.finish()`` when done.
    The trace is stored in a ContextVar so all downstream helpers can access
    it without being passed explicitly.
    """
    lf = get_langfuse()

    trace = lf.trace(
        name="hotel-booking-agent-turn",
        input=user_query,
        session_id=session_id,
        tags=tags or ["hotel-booking"],
        metadata={"session_id": session_id},
    )

    ctx = TraceContext(trace=trace, session_id=session_id, user_query=user_query)

    _active_trace.set(trace)
    _active_trace_ctx.set(ctx)

    return ctx


def get_current_trace() -> Any:
    """Return the active Langfuse trace (or a no-op if none is set)."""
    return _active_trace.get() or _NoopTrace()


def get_current_ctx() -> TraceContext | None:
    """Return the active TraceContext for this turn (may be None)."""
    return _active_trace_ctx.get()


# ---------------------------------------------------------------------------
# Span helpers
# ---------------------------------------------------------------------------


def _safe_text(obj: Any, limit: int = 4000) -> str:
    """Coerce anything to a string and truncate for Langfuse."""
    try:
        s = str(obj)
    except Exception:  # noqa: BLE001
        s = "<unserializable>"
    return s[:limit]


def _extract_usage(response_obj: Any) -> dict:
    """
    Pull token-usage info from a LangChain AI response object.

    Works with ChatGroq (response_metadata) and most other providers.
    """
    usage: dict = {"prompt_tokens": 0, "completion_tokens": 0}

    try:
        meta = getattr(response_obj, "response_metadata", {}) or {}
        token_usage = meta.get("token_usage") or meta.get("usage") or {}

        usage["prompt_tokens"] = (
            token_usage.get("prompt_tokens")
            or token_usage.get("input_tokens")
            or 0
        )
        usage["completion_tokens"] = (
            token_usage.get("completion_tokens")
            or token_usage.get("output_tokens")
            or 0
        )
    except Exception:  # noqa: BLE001
        pass

    return usage


@contextmanager
def llm_generation_span(
    name: str,
    model: str,
    input_data: Any,
) -> Generator[dict, None, None]:
    """
    Context-manager wrapping one LLM invocation.

    Yields a mutable ``result`` dict. After the ``with`` block, callers
    should have set:
        result["response"]  — the raw LangChain AIMessage / structured obj
        result["output"]    — plain-text version of the output (optional)

    Latency is measured automatically.  Token usage is extracted from the
    response object via ``response_metadata`` and rolled up into the parent
    TraceContext.

    Example::

        with llm_generation_span("extraction", model="gpt-oss-20b",
                                  input_data=msg) as r:
            r["response"] = chain.invoke(...)
    """
    trace = get_current_trace()
    ctx = get_current_ctx()
    start = time.perf_counter()

    gen = trace.generation(
        name=name,
        model=model,
        input=_safe_text(input_data),
    )

    result: dict = {"response": None, "output": ""}

    try:
        yield result
    finally:
        latency_ms = (time.perf_counter() - start) * 1_000

        response = result.get("response")
        usage = _extract_usage(response)
        output_text = result.get("output") or _safe_text(
            getattr(response, "content", response)
        )

        # Collect tool_calls if present on the AIMessage
        tool_calls_meta: list = []
        try:
            raw_tcs = getattr(response, "tool_calls", []) or []
            for tc in raw_tcs:
                tool_calls_meta.append(
                    {
                        "name": tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", ""),
                        "args": (
                            tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                        ),
                    }
                )
        except Exception:  # noqa: BLE001
            pass

        try:
            gen.end(
                output=output_text,
                usage={
                    "input": usage["prompt_tokens"],
                    "output": usage["completion_tokens"],
                    "total": usage["prompt_tokens"] + usage["completion_tokens"],
                    "unit": "TOKENS",
                },
                metadata={
                    "latency_ms": round(latency_ms, 2),
                    "tool_calls_emitted": tool_calls_meta,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse gen.end error: %s", exc)

        if ctx is not None:
            ctx.add_usage(usage["prompt_tokens"], usage["completion_tokens"])


@contextmanager
def tool_span(
    tool_name: str,
    tool_input: dict,
) -> Generator[dict, None, None]:
    """
    Context-manager wrapping one tool invocation.

    Yields a mutable ``result`` dict. After the ``with`` block, callers
    should have set:
        result["output"]  — the tool's JSON / string output
        result["error"]   — any error string (or None)

    Example::

        with tool_span("check_availability", args) as r:
            r["output"] = my_tool.run(args)
    """
    trace = get_current_trace()
    ctx = get_current_ctx()
    start = time.perf_counter()

    span = trace.span(
        name=f"tool:{tool_name}",
        input=tool_input,
    )

    result: dict = {"output": "", "error": None}

    try:
        yield result
    finally:
        latency_ms = (time.perf_counter() - start) * 1_000
        has_error = bool(result.get("error"))
        level = "ERROR" if has_error else "DEFAULT"

        try:
            span.end(
                output=_safe_text(result.get("output", "")),
                level=level,
                metadata={
                    "latency_ms": round(latency_ms, 2),
                    "tool": tool_name,
                    "status": "error" if has_error else "success",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse span.end error: %s", exc)

        if ctx is not None:
            ctx.add_tool_call(
                tool_name=tool_name,
                latency_ms=latency_ms,
                result_preview=str(result.get("output", "")),
            )
