# API Monitoring Dashboard using FastAPI

A sample **FastAPI** REST service with a complete monitoring stack: **Prometheus** (metrics + alert rules),
**Blackbox Exporter** (synthetic uptime probes), **Alertmanager** (Email + Slack + optional phone/call),
and a pre-provisioned **Grafana** dashboard. Includes failure simulation with automatic root-cause evidence.

| Component | URL |
|---|---|
| FastAPI (Swagger UI) | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 (alerts: `/alerts`) |
| Alertmanager | http://localhost:9093 |
| Grafana | http://localhost:3000  (login `admin` / `admin123`) |

## 1. Prerequisites
Docker Desktop (with Compose v2), Python 3.10+, Git, a Gmail account (or any SMTP) and a Slack workspace.

## 2. Run the API locally (without Docker) - optional
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest -q                                               # 8 automated tests
```
```bash
curl http://localhost:8000/health
curl -H "X-API-Key: demo-valid-key" http://localhost:8000/users
curl -H "X-API-Key: demo-valid-key" http://localhost:8000/products
curl -i http://localhost:8000/simulate-error             # 500
curl -i "http://localhost:8000/simulate-timeout?delay=5"  # slow (5 s)
curl -i http://localhost:8000/simulate-rate-limit        # 200 x5 then 429
```
`/users`, `/products` and `/errors/recent` require header `X-API-Key: demo-valid-key`.

## 3. Configure notifications
```bash
cp .env.example .env          # then edit .env
```
* **Email (Gmail):** Google Account -> Security -> enable 2-Step Verification -> *App passwords* -> create one -> put it in `SMTP_PASSWORD`.
* **Slack:** https://api.slack.com/apps -> Create App -> *Incoming Webhooks* -> Activate -> *Add New Webhook to Workspace* -> choose `#api-alerts` -> copy URL into `SLACK_WEBHOOK_URL`.
* **Phone/call (optional):** put a webhook URL of a call service (Better Stack on-call, Twilio Studio/Function, Zapier->phone call) in `PHONE_WEBHOOK_URL`. Critical alerts are posted to it.

Generate the Alertmanager config (secrets stay out of Git):
```bash
python scripts/render_alertmanager.py
```

## 4. Start the whole stack
```bash
docker compose up -d --build
docker compose ps                    # all 5 services "running"
```
Open Grafana -> Dashboards -> **FastAPI API Monitoring**. Prometheus -> Status -> Targets: all `UP`.

Generate normal traffic for the dashboard:
```bash
python scripts/generate_traffic.py --duration 300 --rps 2
```

## 5. Failure simulation + alert testing
```bash
python scripts/simulate_failures.py all        # runs scenarios 1-5, waits for each alert to FIRE, writes the report
```
Output: `docs/evidence/failure-test-report.md`. Also test **ApiDown** manually:
```bash
docker compose stop api      # wait ~40 s -> ApiDown alert (Email + Slack)
docker compose start api     # RESOLVED notification
```
Details: [docs/FAILURE_SIMULATION.md](docs/FAILURE_SIMULATION.md).

## 6. Collect proof (deliverables)
Save into `docs/evidence/` (see [docs/EVIDENCE_CHECKLIST.md](docs/EVIDENCE_CHECKLIST.md)): dashboard screenshots, Prometheus alerts page,
Slack message screenshot, email screenshot, `failure-test-report.md`, optional screen recording.

## 7. Documentation
* [Architecture](docs/ARCHITECTURE.md) · [Dashboard](docs/DASHBOARD.md) · [Alert rules](docs/ALERT_RULES.md)
* [Failure simulation](docs/FAILURE_SIMULATION.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Maintenance](docs/MAINTENANCE.md)

## 8. Project layout
```
app/            FastAPI source (main, auth, metrics, failures, ratelimit, db)
tests/          pytest suite
monitoring/     prometheus, alertmanager (template), blackbox, grafana (provisioning + dashboard JSON)
scripts/        render_alertmanager.py, generate_traffic.py, simulate_failures.py
docs/           technical documentation + evidence/
docker-compose.yml, Dockerfile, requirements.txt, .env.example
```
