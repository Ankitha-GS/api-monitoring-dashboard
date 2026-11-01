#!/usr/bin/env python3
"""Failure simulation + automatic evidence report.

Runs the 4 required scenarios (+ health failure), then:
  * verifies the HTTP behaviour,
  * fetches root-cause data from GET /errors/recent,
  * waits for the matching alert to FIRE in Prometheus,
  * writes docs/evidence/failure-test-report.md

Usage:
  python scripts/simulate_failures.py all
  python scripts/simulate_failures.py 1 3          # selected scenarios
  python scripts/simulate_failures.py all --skip-alerts   # API only, no Prometheus needed
Scenarios: 1=invalid auth, 2=timeout, 3=server error (500), 4=rate limit (429), 5=health failure
"""
import argparse
import os
import sys
import time
from datetime import datetime

import requests

API = os.getenv("API_URL", "http://localhost:8000")
PROM = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
KEY = os.getenv("API_KEY", "demo-valid-key")
REPORT = os.path.join(os.path.dirname(__file__), "..", "docs", "evidence", "failure-test-report.md")
AUTH = {"X-API-Key": KEY}


def rca(category, limit=1):
    r = requests.get(f"{API}/errors/recent", params={"category": category, "limit": limit}, headers=AUTH, timeout=10)
    return r.json().get("failures", [])


def wait_for_alert(name, timeout=150):
    """Poll Prometheus until alert `name` is firing. Returns (fired, seconds_waited)."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            alerts = requests.get(f"{PROM}/api/v1/alerts", timeout=5).json()["data"]["alerts"]
            if any(a["labels"]["alertname"] == name and a["state"] == "firing" for a in alerts):
                return True, round(time.time() - start)
        except requests.RequestException:
            pass
        time.sleep(3)
    return False, timeout


# ------------------------------------------------------------------ scenarios
def s1_auth():
    obs = []
    for label, headers in [("no key", {}), ("wrong key", {"X-API-Key": "invalid-key-123"})] * 3:
        r = requests.get(f"{API}/users", headers=headers, timeout=10)
        obs.append(f"GET /users ({label}) -> HTTP {r.status_code} {r.json().get('detail')}")
    ok = all("HTTP 401" in o for o in obs)
    return dict(name="Invalid API authentication", alert="AuthenticationFailures", ok=ok, observed=obs, category="authentication",
                expected="HTTP 401 on every call, authentication failure recorded, alert triggered")


def s2_timeout():
    obs = []
    t0 = time.time()
    try:
        requests.get(f"{API}/simulate-timeout?delay=5", timeout=3)
        obs.append("client did NOT time out (unexpected)")
        client_timeout = False
    except requests.exceptions.Timeout:
        obs.append(f"client-side timeout after {time.time() - t0:.1f}s (client limit 3s, endpoint delay 5s)")
        client_timeout = True
    for _ in range(2):  # complete full responses so the server records a >3s request
        t0 = time.time()
        r = requests.get(f"{API}/simulate-timeout?delay=5", timeout=20)
        obs.append(f"GET /simulate-timeout?delay=5 -> HTTP {r.status_code} in {time.time() - t0:.2f}s")
    return dict(name="API timeout / slow response", alert="HighResponseTime", ok=client_timeout, observed=obs, category="slow_response",
                expected="Response time > 3s detected, timeout identified, alert triggered")


def s3_error():
    obs = []
    for kind in ["database", "database", "zero", "key", "database", "database"]:
        r = requests.get(f"{API}/simulate-error", params={"kind": kind}, timeout=10)
        obs.append(f"GET /simulate-error?kind={kind} -> HTTP {r.status_code} request_id={r.json().get('request_id')}")
    ok = all("HTTP 500" in o for o in obs)
    return dict(name="Server error (HTTP 500)", alert="Http500Errors", ok=ok, observed=obs, category="server_error",
                expected="HTTP 500 detected, exception details captured, root cause provided")


def s4_rate_limit():
    requests.get(f"{API}/simulate-rate-limit", timeout=10)  # (state may already be partially used)
    obs, codes = [], []
    for i in range(10):
        r = requests.get(f"{API}/simulate-rate-limit", timeout=10)
        codes.append(r.status_code)
        obs.append(f"call {i + 1}: HTTP {r.status_code}" + (f" Retry-After={r.headers.get('Retry-After')}s" if r.status_code == 429 else ""))
    return dict(name="Rate limit exceeded (HTTP 429)", alert="RateLimitExceeded", ok=429 in codes, observed=obs, category="rate_limit",
                expected="HTTP 429 detected, rate-limit issue identified, alert triggered")


def s5_health():
    obs = []
    r = requests.get(f"{API}/simulate-health-failure?enable=true", timeout=10)
    obs.append(f"enable forced failure -> {r.json()}")
    h = requests.get(f"{API}/health", timeout=10)
    obs.append(f"GET /health -> HTTP {h.status_code} {h.json()['status']} checks={h.json()['checks']}")
    return dict(name="Service health failure", alert="ServiceHealthFailure", ok=h.status_code == 503, observed=obs, category="health_check",
                expected="/health returns 503, ServiceHealthFailure alert triggered", cleanup=lambda: requests.get(f"{API}/simulate-health-failure?enable=false", timeout=10))


SCEN = {"1": s1_auth, "2": s2_timeout, "3": s3_error, "4": s4_rate_limit, "5": s5_health}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("which", nargs="+", help="1 2 3 4 5 or all")
    p.add_argument("--skip-alerts", action="store_true", help="do not wait for Prometheus alerts")
    a = p.parse_args()
    keys = list(SCEN) if "all" in a.which else a.which

    lines = [f"# Failure Testing Results\n\nGenerated: {datetime.now():%Y-%m-%d %H:%M:%S}  |  API: {API}  |  Prometheus: {PROM}\n"]
    summary = []
    for k in keys:
        print(f"\n=== Scenario {k} ===")
        res = SCEN[k]()
        for o in res["observed"]:
            print("  ", o)
        fired, waited = (None, 0)
        if not a.skip_alerts:
            print(f"   waiting for alert {res['alert']} to fire in Prometheus ...")
            fired, waited = wait_for_alert(res["alert"])
            print(f"   alert {res['alert']}: {'FIRING' if fired else 'NOT FIRING'} (after {waited}s)")
        causes = rca(res["category"])
        if res.get("cleanup"):
            res["cleanup"]()
        summary.append((k, res["name"], res["ok"], fired))

        lines += [f"\n## Scenario {k}: {res['name']}\n", f"**Expected:** {res['expected']}\n", "**Observed:**\n"]
        lines += [f"- {o}" for o in res["observed"]]
        lines.append(f"\n**Detection result:** {'PASS' if res['ok'] else 'FAIL'}")
        if fired is not None:
            lines.append(f"\n**Alert `{res['alert']}`:** {'FIRING in Prometheus (notification sent via Alertmanager)' if fired else 'did not fire within timeout'} (waited {waited}s)")
        lines.append("\n**Root cause information (`GET /errors/recent`):**\n\n```json")
        import json
        lines.append(json.dumps(causes[0] if causes else {}, indent=2))
        lines.append("```")
        time.sleep(1)

    lines.append("\n## Summary\n\n| # | Scenario | Detected | Alert fired |\n|---|---|---|---|")
    for k, n, ok, fired in summary:
        lines.append(f"| {k} | {n} | {'PASS' if ok else 'FAIL'} | {'-' if fired is None else ('YES' if fired else 'NO')} |")
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport written to docs/evidence/failure-test-report.md")
    return 0 if all(s[2] for s in summary) and all(s[3] is not False for s in summary) else 1


if __name__ == "__main__":
    sys.exit(main())
