# API Monitoring Dashboard Using FastAPI

A real-time API monitoring and observability platform built with **FastAPI, Prometheus, Grafana, Blackbox Exporter, and Alertmanager**. The system monitors API availability, response times, request metrics, and failures while providing automated alerts and root-cause information.

## Key Features

- **API Monitoring:** Tracks API availability, uptime, response times, request counts, and HTTP status codes.
- **Real-Time Dashboard:** Visualizes API performance, error rates, latency trends, and service health using Grafana.
- **Metrics Collection:** Uses Prometheus to collect and evaluate application and infrastructure metrics.
- **Synthetic Monitoring:** Uses Blackbox Exporter to monitor endpoint availability and response latency.
- **Automated Alerting:** Configures alerts for API downtime, slow responses, HTTP 500 errors, high failure rates, authentication failures, and rate limiting.
- **Notifications:** Supports email and Discord notifications through Alertmanager.
- **Failure Simulation:** Simulates API errors, timeouts, authentication failures, and rate-limit scenarios.
- **Root-Cause Analysis:** Captures failure categories, request IDs, timestamps, error messages, and diagnostic information.

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Monitoring | Prometheus, Blackbox Exporter |
| Visualization | Grafana |
| Alert Management | Alertmanager |
| Notifications | Gmail SMTP, Discord Webhooks |
| Containerization | Docker, Docker Compose |
| Testing | Pytest |
| Version Control | Git, GitHub |

## Architecture

The application exposes API endpoints and Prometheus metrics. Prometheus collects application metrics and evaluates alert rules, while Blackbox Exporter performs synthetic endpoint checks. Grafana visualizes monitoring data, and Alertmanager distributes notifications when configured alert conditions are met.

## Application Endpoints

| Endpoint | Description |
|---|---|
| `/` | API service information |
| `/health` | Service health check |
| `/users` | Retrieve user information |
| `/products` | Retrieve product information |
| `/metrics` | Prometheus metrics |
| `/simulate-error` | Simulate an HTTP 500 error |
| `/simulate-timeout` | Simulate a slow API response |
| `/simulate-rate-limit` | Test HTTP 429 rate limiting |
| `/errors/recent` | Retrieve recent failure and root-cause information |

Protected endpoints require a valid `X-API-Key` header.

## Monitoring Services

| Service | Local URL |
|---|---|
| FastAPI Swagger UI | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| Grafana | http://localhost:3000 |

Grafana dashboard: **FastAPI API Monitoring**

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.10 or later (for optional local execution)

### 1. Clone the repository

```bash
git clone https://github.com/Ankitha-GS/api-monitoring-dashboard.git
cd api-monitoring-dashboard
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Update the `.env` file with your notification configuration. Add your SMTP credentials and Discord webhook URL if you want to enable notifications.

**Never commit your `.env` file or expose credentials in GitHub.**

### 3. Generate Alertmanager configuration

```bash
python scripts/render_alertmanager.py
```

### 4. Start the monitoring stack

```bash
docker compose up -d --build
```

Check the running containers:

```bash
docker compose ps
```

### 5. Access the dashboard

Open Grafana at http://localhost:3000 and navigate to **Dashboards → FastAPI API Monitoring**.

## Failure Simulation and Alert Testing

The project supports the following failure scenarios:

| Scenario | Expected Detection |
|---|---|
| Authentication failure | HTTP 401 / 403 |
| API timeout | Slow response detection |
| Server error | HTTP 500 |
| Rate limiting | HTTP 429 |
| API downtime | Availability alert |
| Service health failure | Unhealthy service status |

Prometheus evaluates configured alert rules, and Alertmanager sends notifications through the configured channels.

## Testing

Run the automated test suite:

```bash
pytest -q
```

Generate sample API traffic:

```bash
python scripts/generate_traffic.py --duration 300 --rps 2
```

## Project Structure

```text
api-monitoring-dashboard/
│
├── app/                  # FastAPI application
├── tests/                # Automated tests
├── monitoring/
│   ├── prometheus/       # Scrape configuration and alert rules
│   ├── grafana/          # Dashboard and provisioning
│   ├── alertmanager/     # Notification configuration
│   └── blackbox/         # Synthetic monitoring configuration
│
├── scripts/              # Traffic generation and failure simulation
├── docs/                 # Technical documentation and evidence
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Documentation

Detailed project documentation is available in the [`docs/`](docs/) directory:

- [System Architecture](docs/ARCHITECTURE.md)
- [Grafana Dashboard](docs/DASHBOARD.md)
- [Alert Rules](docs/ALERT_RULES.md)
- [Failure Simulation](docs/FAILURE_SIMULATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Maintenance](docs/MAINTENANCE.md)
- [Evidence Checklist](docs/EVIDENCE_CHECKLIST.md)

## Future Improvements

- Add additional notification integrations such as Slack.
- Extend monitoring with distributed tracing.
- Introduce historical performance analysis and reporting.
- Add advanced anomaly detection for API performance.

## Author

**Ankitha G S**

[GitHub](https://github.com/Ankitha-GS)
