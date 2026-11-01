# TEMPLATE - do not edit the generated alertmanager.yml (it contains secrets and is git-ignored).
# Render with:  python scripts/render_alertmanager.py
global:
  resolve_timeout: 2m
  smtp_smarthost: '${SMTP_HOST}:${SMTP_PORT}'
  smtp_from: '${ALERT_EMAIL_FROM}'
  smtp_auth_username: '${SMTP_USERNAME}'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true

route:
  receiver: team-notifications
  group_by: ['alertname']
  group_wait: 5s
  group_interval: 30s
  repeat_interval: 1h
  routes:
    - matchers: ['severity="critical"']
      receiver: critical-notifications

inhibit_rules:
  - source_matchers: ['alertname="ApiDown"']
    target_matchers: ['alertname=~"HighFailureRate|HighProbeLatency|HighResponseTime"']

receivers:
  - name: team-notifications
    email_configs:
      - to: '${ALERT_EMAIL_TO}'
        send_resolved: true
        headers:
          Subject: '[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }} ({{ .CommonLabels.severity }})'
__CHAT_TEAM__

  - name: critical-notifications
    email_configs:
      - to: '${ALERT_EMAIL_TO}'
        send_resolved: true
        headers:
          Subject: '[CRITICAL][{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
__CHAT_CRITICAL__
__PHONE_WEBHOOK__