"""
Opik Tracing - Span-per-step tracing for the orchestrator pipeline.

Creates a trace per process_prompt call with child spans per step.
Degrades gracefully if opik is not installed.

Usage:
    from src.opik_integration.tracker import OpikTracker

    tracker = OpikTracker()
    tracker.start_trace("chicken biryani for 4")
    tracker.start_span("step_ingredients")
    # ... do work ...
    tracker.end_span({"ingredient_count": 13})
    tracker.end_trace(bundle_dict)
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any

# Try to import opik; if not installed, all operations are no-ops
try:
    import opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False


@dataclass
class SpanRecord:
    """Local record of a span for debugging."""
    name: str
    start_time: float
    end_time: float = 0.0
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    duration_ms: float = 0.0


class OpikTracker:
    """
    Tracing wrapper that logs orchestrator steps to Opik.

    If opik is not installed, all methods are no-ops and the
    local span log is still available for debugging.
    """

    def __init__(self, project_name: str = "conscious-cart-coach"):
        self.project_name = project_name
        self.enabled = OPIK_AVAILABLE and os.getenv("OPIK_ENABLED", "0") == "1"
        self._trace = None
        self._current_span = None
        self._spans: list[SpanRecord] = []
        self._trace_start: float = 0.0

        if self.enabled:
            opik.configure(project_name=project_name)

    def start_trace(self, user_prompt: str, metadata: dict | None = None):
        """Start a new trace for a user request."""
        self._trace_start = time.time()
        self._spans = []

        if self.enabled:
            self._trace = opik.trace(
                name="process_prompt",
                input={"user_prompt": user_prompt, **(metadata or {})},
            )

    def start_span(self, name: str, inputs: dict | None = None):
        """Start a child span within the current trace."""
        span = SpanRecord(name=name, start_time=time.time(), inputs=inputs or {})
        self._spans.append(span)

        if self.enabled and self._trace:
            self._current_span = self._trace.span(
                name=name,
                input=inputs or {},
            )

    def end_span(self, outputs: dict | None = None):
        """End the current span with outputs."""
        if self._spans:
            span = self._spans[-1]
            span.end_time = time.time()
            span.outputs = outputs or {}
            span.duration_ms = (span.end_time - span.start_time) * 1000

        if self.enabled and self._current_span:
            self._current_span.end(output=outputs or {})
            self._current_span = None

    def end_trace(self, outputs: dict | None = None):
        """End the trace with final outputs."""
        if self.enabled and self._trace:
            self._trace.end(output=outputs or {})
            self._trace = None

    def get_spans(self) -> list[SpanRecord]:
        """Get local span records for debugging."""
        return self._spans

    def get_timing_summary(self) -> dict[str, float]:
        """Get timing breakdown by span name."""
        return {s.name: s.duration_ms for s in self._spans}


def init_opik(project_name: str = "conscious-cart-coach") -> OpikTracker:
    """Initialize and return an Opik tracker."""
    return OpikTracker(project_name)
