# Monitoring Architecture

```
            +-------------------+   scrape /metrics (5s)    +--------------+   alerts    +--------------+--> Email (SMTP)
 clients -->|  FastAPI :8000    |<--------------------------|  Prometheus  |------------>| Alertmanager |--> Slack webhook
            |  /health /users...|                           |  :9090       |             |  :9093       |--> Phone webhook (optional)
            +-------------------+                           +------+-------+             +--------------+
                     ^                                             |  ^
                     | HTTP probe /health, /users (5s)             |  | PromQL
               +-----+------+                                      v  |
               | Blackbox   |--- probe_success, probe_duration --->+  +---------+
               | Exporter   |                                         | Grafana |  dashboard :3000
               +------------+                                         +---------+
```

## What is monitored and how
| Requirement | Source | Metric |
|---|---|---|
| API availability | Blackbox probe + `up` | `probe_success`, `up{job="fastapi"}` |
| Response time | App histogram + probe | `http_request_duration_seconds_*`, `probe_duration_seconds` |
| HTTP status codes | App counter | `http_requests_total{status}` |
| Error percentage / failed requests | derived | `status=~"[45].."` / total |
| Server health | psutil gauges + health endpoint | `server_cpu_percent`, `server_memory_percent`, `server_disk_percent`, `service_health_status` |
| Root cause | App failure registry | `api_failures_total{category}` + `GET /errors/recent` + JSON logs |

## Design decisions
* **Two viewpoints**: internal metrics (what the app sees) and external probes (what a user sees). If the app dies, internal metrics vanish but the probe still reports it.
* **Failure registry**: every failure is classified (`authentication`, `rate_limit`, `server_error`, `slow_response`, `health_check`) with request id, path, exception type, message and traceback - this is the root-cause data.
* **Route templates** are used as the `path` label (not raw URLs) to avoid high-cardinality metrics.
* Counters are **pre-initialised to 0** so `increase()` catches the very first event.
* The API runs a **single worker** because metrics and rate-limit state are in process memory (for multiple workers use `prometheus_client` multiprocess mode or Redis).
* Scrape/evaluation interval is 5s for a fast demo; use 15-30s in production.
