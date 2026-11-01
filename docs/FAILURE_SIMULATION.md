# Failure Simulation & Root Cause Analysis

Prerequisite: stack running (`docker compose up -d --build`) and optional traffic (`python scripts/generate_traffic.py --duration 600`).
Automated: `python scripts/simulate_failures.py all` (writes `docs/evidence/failure-test-report.md`).

| # | Scenario | Trigger | Detected as | Alert | Root cause source |
|---|---|---|---|---|---|
| 1 | Invalid authentication | `curl http://localhost:8000/users` and `curl -H "X-API-Key: bad" ...` | HTTP **401**, `error: missing_api_key / invalid_api_key` | AuthenticationFailures (+HighFailureRate) | `/errors/recent?category=authentication` (client IP, reason, request id) |
| 2 | API timeout | `curl -m 3 "localhost:8000/simulate-timeout?delay=5"` -> curl exit 28; also run without `-m` | request > 3s; latency panel spikes; client timeout | HighResponseTime | `/errors/recent?category=slow_response` (duration, path); server health panels to rule out CPU/memory |
| 3 | Server error | `curl localhost:8000/simulate-error` (also `?kind=zero`, `?kind=key`) | HTTP **500** | Http500Errors (+HighFailureRate) | `/errors/recent?category=server_error` (exception type, message, traceback, request id); `docker compose logs api` |
| 4 | Rate limit | call `/simulate-rate-limit` 10x quickly | HTTP **429** + `Retry-After` | RateLimitExceeded | `/errors/recent?category=rate_limit` (client, limit, retry-after) |
| 5 | Health failure | `curl "localhost:8000/simulate-health-failure?enable=true"` | `/health` = 503 | ServiceHealthFailure (restore with `enable=false`) | `/health` JSON `checks` |
| 6 | Downtime | `docker compose stop api` | probe_success=0, target DOWN | ApiDown (restore: `docker compose start api`) | `docker compose ps/logs` |

Read root-cause data:
```bash
curl -s -H "X-API-Key: demo-valid-key" "http://localhost:8000/errors/recent?category=server_error&limit=3" | python -m json.tool
```

## Sample root-cause analysis - Scenario 3 (HTTP 500)
* **Symptom:** Http500Errors alert; 5xx line rises on the Error Trend panel; Failures-by-category shows `server_error`.
* **Evidence:** `exception_type: RuntimeError`, `message: Simulated failure: could not acquire connection from database pool (pool exhausted, 20/20 in use)`, traceback shows `app/main.py simulate_error`, `request_id` ties it to the log line.
* **Root cause:** database connection pool exhausted in `/simulate-error` handler.
* **Fix / prevention:** increase pool size or release connections, add timeouts + retries, add alert on pool usage.

## What to capture as proof
Slack alert, email alert, Prometheus *Alerts* page (firing), Grafana during each scenario, and the generated report.
