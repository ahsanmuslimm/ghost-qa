"""Prometheus metrics and instrumentation middleware.

Exposes HTTP request counters, latency histograms and an active-request
gauge. The exporter is mounted at /metrics in app.main (outside /api,
so it bypasses JWT auth and is scrapeable by Prometheus).
"""
import time

from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "ghost_qa_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "ghost_qa_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)
ACTIVE_REQUESTS = Gauge(
    "ghost_qa_active_requests",
    "Number of in-flight requests",
)

# Paths with unbounded cardinality that must not become metric labels
_SKIP_PREFIXES = ("/metrics", "/static", "/docs", "/openapi.json", "/redoc")
_MAX_LABEL_LEN = 128


def _endpoint_label(path: str) -> str:
    """Normalize the request path for use as a low-cardinality label."""
    for prefix in _SKIP_PREFIXES:
        if path.startswith(prefix):
            return prefix
    return path[:_MAX_LABEL_LEN]


async def metrics_middleware(request: Request, call_next):
    """Record count/latency/active-request metrics for every HTTP request."""
    endpoint = _endpoint_label(request.url.path)
    if endpoint in _SKIP_PREFIXES:
        return await call_next(request)

    ACTIVE_REQUESTS.inc()
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        ACTIVE_REQUESTS.dec()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(
            time.perf_counter() - start
        )
        REQUEST_COUNT.labels(request.method, endpoint, str(status_code)).inc()
