# Troubleshooting Guide

| Problem | Check / Fix |
|---|---|
| `docker compose up` fails: alertmanager.yml is a directory | The file did not exist. Run `python scripts/render_alertmanager.py`, `rm -rf monitoring/alertmanager/alertmanager.yml` if it is a folder, then `docker compose up -d` |
| Alertmanager container restarts | `docker compose logs alertmanager` -> usually YAML/SMTP error or empty Slack URL in `.env`; re-render |
| Targets DOWN in Prometheus (Status -> Targets) | `docker compose ps`; `docker compose logs api`; names must be `api:8000` inside the Docker network |
| Grafana shows "No data" | Prometheus datasource healthy? Generate traffic. Widen time range. Counters appear after first scrape (5-10s) |
| Alert stays *Pending* | `for:` duration not yet elapsed (see ALERT_RULES.md) |
| Alert firing but no Slack | Alertmanager UI -> status; `docker compose logs alertmanager | grep -i slack`; wrong webhook/channel |
| Alert firing but no email | Gmail needs **App Password** (not the normal password), port 587. Check spam. Logs: `grep -i smtp` |
| `/users` returns 401 | Add `-H "X-API-Key: demo-valid-key"` (or whatever is in `API_KEYS`). The blackbox probe key in `blackbox.yml` must match |
| HighFailureRate does not fire | Needs > 10% failures **and** > 0.05 req/s overall; run `simulate_failures.py 3` or traffic generator |
| Rate-limit demo returns 200 only | Window is 30 s per client; wait 30 s and re-run |
| Port already in use | Change published ports in `docker-compose.yml` (3000, 8000, 9090, 9093, 9115) |
| Reload Prometheus config | `curl -X POST http://localhost:9090/-/reload` |
| Reset everything | `docker compose down -v` |

General workflow: *alert -> dashboard (which metric/endpoint/status?) -> `/errors/recent` (category, request id) -> `docker compose logs api` -> fix -> confirm RESOLVED notification.*
