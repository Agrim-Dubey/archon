"""Prometheus metrics middleware and collectors."""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

HTTP_REQUESTS_TOTAL = Counter(
    "archon_http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "archon_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ACTIVE_WS_CONNECTIONS = Gauge(
    "archon_active_ws_connections",
    "Active real-time WebSocket interview connections",
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for capturing request counts and response latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.time() - start_time
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=endpoint, status=status_code
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=endpoint
            ).observe(duration)
