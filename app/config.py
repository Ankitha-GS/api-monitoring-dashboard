"""Central configuration (all values can be overridden by environment variables)."""
import os

API_KEYS = {k.strip() for k in os.getenv("API_KEYS", "demo-valid-key").split(",") if k.strip()}
SLOW_THRESHOLD_SECONDS = float(os.getenv("SLOW_THRESHOLD_SECONDS", "3"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "5"))          # requests ...
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "30"))   # ... per N seconds per client
DB_PATH = os.getenv("DB_PATH", "data/app.db")
APP_VERSION = "1.0.0"
