import re

from .conftest import HEADERS


def metric_value(text: str, pattern: str) -> float:
    m = re.search(pattern + r"\s+([0-9.e+-]+)", text)
    return float(m.group(1)) if m else 0.0


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_users_requires_auth(client):
    assert client.get("/users").status_code == 401
    assert client.get("/users", headers={"X-API-Key": "wrong"}).status_code == 401


def test_users_and_products_ok(client):
    assert len(client.get("/users", headers=HEADERS).json()["data"]) == 4
    assert len(client.get("/products", headers=HEADERS).json()["data"]) == 4


def test_simulate_error_returns_500_and_captures_rca(client):
    r = client.get("/simulate-error")
    assert r.status_code == 500
    assert "request_id" in r.json()
    rca = client.get("/errors/recent?category=server_error&limit=1", headers=HEADERS).json()
    assert rca["failures"][0]["exception_type"] == "RuntimeError"
    assert "pool exhausted" in rca["failures"][0]["message"]


def test_simulate_timeout_marks_slow(client):
    r = client.get("/simulate-timeout?delay=0.4")
    assert r.status_code == 200
    text = client.get("/metrics").text
    assert metric_value(text, r'http_slow_requests_total\{path="/simulate-timeout"\}') >= 1


def test_rate_limit_429(client):
    codes = [client.get("/simulate-rate-limit").status_code for _ in range(8)]
    assert codes[:5] == [200] * 5
    assert codes[5:] == [429] * 3
    r = client.get("/simulate-rate-limit")
    assert "retry-after" in r.headers


def test_health_failure_toggle(client):
    assert client.get("/simulate-health-failure?enable=true").status_code == 200
    assert client.get("/health").status_code == 503
    client.get("/simulate-health-failure?enable=false")
    assert client.get("/health").status_code == 200


def test_metrics_exposed(client):
    client.get("/health")
    text = client.get("/metrics").text
    for name in ("http_requests_total", "http_request_duration_seconds_bucket", "service_health_status", "server_cpu_percent"):
        assert name in text
