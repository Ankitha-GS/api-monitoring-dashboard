# Maintenance Process

| Frequency | Task |
|---|---|
| Daily | Look at dashboard + Prometheus *Alerts* page; review any resolved alerts |
| Weekly | Review noisy/never-firing alerts and tune thresholds; send a test alert to verify Slack/Email still work (`simulate_failures.py 3`) |
| Monthly | Update image versions in `docker-compose.yml` and `pip` deps, run `pytest`, re-deploy; rotate API keys and SMTP/Slack secrets; back up Grafana volume |
| Quarterly | Review SLOs (uptime target, latency target), disk usage of Prometheus (`--storage.tsdb.retention.time`) |

* **Adding an endpoint:** add it to `_EXPECTED` in `app/metrics.py` (pre-initialises its counters); no other change needed.
* **Adding an alert:** edit `alert_rules.yml`, validate with `promtool check rules`, reload Prometheus, add a scenario to `scripts/simulate_failures.py`.
* **Changing contacts/webhooks:** edit `.env`, run `python scripts/render_alertmanager.py`, `docker compose restart alertmanager`.
* **Dashboard changes:** edit in Grafana, export JSON to `monitoring/grafana/dashboards/`, commit.
* **Secrets:** never commit `.env` or the generated `alertmanager.yml` (both git-ignored).
* **Scaling notes:** for production use multiple API workers with Prometheus multiprocess mode, Redis-based rate limiting, longer scrape interval and remote storage.
