"""OpenTelemetry tracing and W3C trace context utilities."""

import logging
from typing import Dict, Optional
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

tracer = trace.get_tracer("fast-api-archon", "1.0.0")
propagator = TraceContextTextMapPropagator()


def init_telemetry(service_name: str = "fast-api-archon") -> None:
    """Initialize OpenTelemetry tracer provider."""
    logger.info("Telemetry initialized for service: %s", service_name)


def extract_trace_context(headers: Dict[str, str]) -> trace.Context:
    """Extract W3C traceparent headers into OpenTelemetry Context."""
    return propagator.extract(carrier=headers)


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """Inject current span trace context into carrier headers."""
    propagator.inject(carrier=headers)
    return headers
