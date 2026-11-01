#!/usr/bin/env python3
"""Render monitoring/alertmanager/alertmanager.yml from the template + values in .env

Chat channel (both are FREE):  SLACK_WEBHOOK_URL (free Slack workspace)  and/or  DISCORD_WEBHOOK_URL.
Leave a variable empty to disable that channel. Email is always required.
"""
import os
import sys
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "ALERT_EMAIL_FROM", "ALERT_EMAIL_TO"]
OPTIONAL = ["SLACK_WEBHOOK_URL", "SLACK_CHANNEL", "DISCORD_WEBHOOK_URL", "PHONE_WEBHOOK_URL"]

SLACK = """    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '${SLACK_CHANNEL}'
        send_resolved: true
        title: '__TITLE__[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
        text: |-
          {{ range .Alerts }}*{{ .Annotations.summary }}*
          {{ .Annotations.description }}
          *Root cause hint:* {{ .Annotations.root_cause }}
          {{ end }}
"""
DISCORD = """    discord_configs:
      - webhook_url: '${DISCORD_WEBHOOK_URL}'
        send_resolved: true
        title: '__TITLE__[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
        message: |-
          {{ range .Alerts }}**{{ .Annotations.summary }}**
          {{ .Annotations.description }}
          **Root cause hint:** {{ .Annotations.root_cause }}
          {{ end }}
"""


def load_env(path: Path) -> dict:
    values = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    for k in REQUIRED + OPTIONAL:
        if k in os.environ:
            values[k] = os.environ[k]
    return values


def main() -> int:
    env = load_env(ROOT / ".env")
    missing = [k for k in REQUIRED if not env.get(k)]
    if missing:
        print(f"ERROR: missing values in .env: {', '.join(missing)}")
        return 1
    env.setdefault("SLACK_CHANNEL", "#api-alerts")
    env["SLACK_CHANNEL"] = env["SLACK_CHANNEL"] or "#api-alerts"
    slack_on = bool(env.get("SLACK_WEBHOOK_URL")) and "XXX/YYY" not in env["SLACK_WEBHOOK_URL"]
    discord_on = bool(env.get("DISCORD_WEBHOOK_URL"))
    if not (slack_on or discord_on):
        print("ERROR: set SLACK_WEBHOOK_URL or DISCORD_WEBHOOK_URL in .env (both free).")
        return 1

    def chat(title_prefix: str) -> str:
        out = (SLACK if slack_on else "") + (DISCORD if discord_on else "")
        return out.replace("__TITLE__", title_prefix)

    phone = env.get("PHONE_WEBHOOK_URL", "")
    phone_block = f"    webhook_configs:\n      - url: '{phone}'\n        send_resolved: false\n" if phone else ""

    tpl = (ROOT / "monitoring/alertmanager/alertmanager.yml.tpl").read_text()
    tpl = (tpl.replace("__CHAT_TEAM__", chat(""))
              .replace("__CHAT_CRITICAL__", chat(":rotating_light: " if slack_on and not discord_on else "CRITICAL "))
              .replace("__PHONE_WEBHOOK__", phone_block))
    target = ROOT / "monitoring/alertmanager/alertmanager.yml"
    target.write_text(Template(tpl).substitute({**env, "SLACK_WEBHOOK_URL": env.get("SLACK_WEBHOOK_URL", ""),
                                                "DISCORD_WEBHOOK_URL": env.get("DISCORD_WEBHOOK_URL", "")}))
    print(f"Generated {target.relative_to(ROOT)} | email: ON | slack: {'ON' if slack_on else 'off'} | "
          f"discord: {'ON' if discord_on else 'off'} | phone: {'ON' if phone else 'off'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())