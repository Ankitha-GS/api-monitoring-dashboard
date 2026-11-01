#!/usr/bin/env python3
"""Generate normal (successful) traffic so the dashboard has data.
Usage: python scripts/generate_traffic.py --duration 300 --rps 2
"""
import argparse
import os
import random
import time

import requests

API = os.getenv("API_URL", "http://localhost:8000")
KEY = os.getenv("API_KEY", "demo-valid-key")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--duration", type=int, default=300, help="seconds to run")
    p.add_argument("--rps", type=float, default=2.0, help="requests per second")
    a = p.parse_args()
    end, sent, ok = time.time() + a.duration, 0, 0
    print(f"Sending ~{a.rps} req/s to {API} for {a.duration}s (Ctrl+C to stop)")
    try:
        while time.time() < end:
            path = random.choice(["/health", "/users", "/products"])
            try:
                r = requests.get(API + path, headers={"X-API-Key": KEY}, timeout=5)
                ok += r.status_code == 200
            except requests.RequestException as e:
                print("request failed:", e)
            sent += 1
            time.sleep(1 / a.rps)
    except KeyboardInterrupt:
        pass
    print(f"Done. sent={sent} ok={ok}")


if __name__ == "__main__":
    main()
