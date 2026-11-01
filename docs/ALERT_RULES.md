# Alert Rules (`monitoring/prometheus/alert_rules.yml`)

| Alert | Severity | Condition | For | Required item |
|---|---|---|---|---|
| ApiDown | critical | target `up==0` or `/health` probe failing (and not just an unhealthy 503) | 30s | API downtime |
| HighResponseTime | warning | any request slower than 3s in last 2m (`http_slow_requests_total`) | 0s | Response time > 3s |
| HighProbeLatency | warning | synthetic probe duration > 3s | 15s | Response time > 3s (external view) |
| Http500Errors | critical | any HTTP 500 in last 2m | 0s | HTTP 500 errors |
| HighFailureRate | critical | 4xx+5xx > 10% of requests (2m) and traffic > 0.05 req/s | 30s | Increased failure rate |
| ServiceHealthFailure | critical | `service_health_status == 0` | 15s | Service health failure |
| AuthenticationFailures | warning | any 401/403 in last 2m | 0s | Scenario 1 |
| RateLimitExceeded | warning | any 429 in last 2m | 0s | Scenario 4 |

## Routing (`alertmanager.yml.tpl`)
* All alerts -> `team-notifications` (Email + Slack). `severity=critical` -> `critical-notifications` (Email + Slack + optional phone webhook).
* `group_wait 5s`, `group_interval 30s`, `repeat_interval 1h`, `send_resolved: true` (you also get a RESOLVED message).
* Inhibition: `ApiDown` suppresses `HighFailureRate`, `HighProbeLatency`, `HighResponseTime` to avoid alert storms.
* Each alert carries `summary`, `description` and a `root_cause` hint shown in the Slack/email body.

## Tuning
Edit thresholds in `alert_rules.yml`, then reload without restart: `curl -X POST localhost:9090/-/reload`.
Check rules: `docker compose exec prometheus promtool check rules /etc/prometheus/alert_rules.yml`.
Test notification channels: Alertmanager UI -> or run `python scripts/simulate_failures.py 3`.
