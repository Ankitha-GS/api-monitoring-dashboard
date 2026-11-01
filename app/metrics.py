"""Prometheus metrics definitions + helpers."""
import time

import psutil
from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5, 10, 30),
)
IN_PROGRESS = Gauge("http_requests_in_progress", "Requests currently being processed")
SLOW = Counter("http_slow_requests_total", "Requests slower than SLOW_THRESHOLD_SECONDS", ["path"])
FAILURES = Counter("api_failures_total", "Classified failures (for root cause analysis)", ["category"])
HEALTH = Gauge("service_health_status", "Overall service health: 1 = healthy, 0 = unhealthy")

# Server health gauges (evaluated at scrape time)
_START = time.time()
Gauge("app_uptime_seconds", "Seconds since the API process started").set_function(lambda: time.time() - _START)
Gauge("server_cpu_percent", "Host CPU utilisation percent").set_function(lambda: psutil.cpu_percent(interval=None))
Gauge("server_memory_percent", "Host memory utilisation percent").set_function(lambda: psutil.virtual_memory().percent)
Gauge("server_disk_percent", "Root disk utilisation percent").set_function(lambda: psutil.disk_usage("/").percent)
Gauge("app_memory_rss_bytes", "API process resident memory (bytes)").set_function(lambda: psutil.Process().memory_info().rss)

FAILURE_CATEGORIES = ["authentication", "rate_limit", "server_error", "slow_response", "health_check"]

# Counters must exist with value 0 *before* the first event, otherwise Prometheus'
# increase()/rate() miss the very first increment. We pre-create the expected series.
_EXPECTED = {
    "/health": [200, 503],
    "/users": [200, 401],
    "/products": [200, 401],
    "/errors/recent": [200, 401],
    "/simulate-error": [500],
    "/simulate-timeout": [200],
    "/simulate-rate-limit": [200, 429],
    "/simulate-health-failure": [200],
}


def preinitialise() -> None:
    for path, statuses in _EXPECTED.items():
        for status in statuses:
            REQUESTS.labels("GET", path, str(status))
        SLOW.labels(path)
    for category in FAILURE_CATEGORIES:
        FAILURES.labels(category)
    HEALTH.set(1)
    psutil.cpu_percent(interval=None)  # prime CPU counter


preinitialise()
