# Dashboard Configuration

Grafana is **auto-provisioned**: datasource (`monitoring/grafana/provisioning/datasources/prometheus.yml`) and dashboard JSON
(`monitoring/grafana/dashboards/api-monitoring.json`). Open http://localhost:3000 -> Dashboards -> *FastAPI API Monitoring*
(login `admin` / `admin123`, auto-refresh 5s, default range 30 min).

| Panel | PromQL |
|---|---|
| Current API Status (UP/DOWN) | `min(probe_success{job="blackbox-health"})` |
| API Uptime % | `avg_over_time(probe_success{job="blackbox-health"}[$__range]) * 100` |
| Avg Response Time | `sum(increase(http_request_duration_seconds_sum[$__range])) / sum(increase(http_request_duration_seconds_count[$__range]))` |
| Total API Requests | `round(sum(increase(http_requests_total[$__range])))` |
| Failed Requests | `round(sum(increase(http_requests_total{status=~"[45].."}[$__range])))` |
| Error Percentage | failed / total * 100 |
| Request rate by status code | `sum by (status) (rate(http_requests_total[1m]))` |
| Error trend | 5xx and 4xx rates over time |
| Response time avg/p95/p99 | `histogram_quantile(0.95, sum by (le)(rate(http_request_duration_seconds_bucket[1m])))` |
| Failures by root-cause category | `sum by (category)(increase(api_failures_total[1m]))` |
| Server health | `server_cpu_percent`, `server_memory_percent`, `server_disk_percent` |
| Service health | `service_health_status`, `probe_success` |
| Active alerts | `ALERTS{alertstate=~"firing\|pending"}` |

Stat panels use the **selected time range** (`$__range`): change the picker (top right) to compute uptime/requests for 5m, 1h, 24h...
To edit: change the panel in Grafana, *Save dashboard -> Export -> JSON* and replace the JSON file so it stays version-controlled.
