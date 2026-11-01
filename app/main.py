"""Sample FastAPI service instrumented for monitoring (Prometheus metrics, JSON logs, RCA buffer)."""
import asyncio
import logging
import time
import traceback
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import config, db, ratelimit
from .auth import verify_api_key
from .failures import RECENT, record_failure
from .metrics import HEALTH, IN_PROGRESS, LATENCY, REQUESTS, SLOW

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("api")

app = FastAPI(title="Monitored Sample API", version=config.APP_VERSION)
db.init_db()
_started = time.time()
_state = {"forced_unhealthy": False, "last_healthy": True}


# --------------------------------------------------------------------------- middleware
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    request.state.request_id = uuid.uuid4().hex[:12]
    start = time.perf_counter()
    IN_PROGRESS.inc()
    try:
        response = await call_next(request)
    except Exception as exc:  # unhandled exception -> HTTP 500 with captured details
        tb_lines = traceback.format_exc().strip().splitlines()
        record_failure(
            "server_error",
            request_id=request.state.request_id,
            method=request.method,
            path=request.url.path,
            status=500,
            exception_type=type(exc).__name__,
            message=str(exc),
            traceback=tb_lines[-10:],
        )
        response = JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "request_id": request.state.request_id},
        )
    finally:
        IN_PROGRESS.dec()

    duration = time.perf_counter() - start
    route = request.scope.get("route")
    path = route.path if route else "unmatched"  # route template keeps label cardinality low
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    LATENCY.labels(request.method, path).observe(duration)

    if duration > config.SLOW_THRESHOLD_SECONDS:
        SLOW.labels(path).inc()
        record_failure(
            "slow_response",
            request_id=request.state.request_id,
            method=request.method,
            path=path,
            status=response.status_code,
            duration_seconds=round(duration, 3),
            threshold_seconds=config.SLOW_THRESHOLD_SECONDS,
        )

    response.headers["X-Request-ID"] = request.state.request_id
    return response


# --------------------------------------------------------------------------- helpers
def evaluate_health() -> tuple[bool, dict]:
    db_ok = db.ping()
    forced = _state["forced_unhealthy"]
    healthy = db_ok and not forced
    HEALTH.set(1 if healthy else 0)
    checks = {"database": "ok" if db_ok else "failed", "forced_failure": forced}
    if _state["last_healthy"] and not healthy:  # log only on transition (avoid flooding)
        record_failure("health_check", path="/health", status=503, checks=checks)
    _state["last_healthy"] = healthy
    return healthy, checks


# --------------------------------------------------------------------------- endpoints
@app.get("/")
def root():
    return {"service": "monitored-sample-api", "version": config.APP_VERSION, "docs": "/docs", "metrics": "/metrics"}


@app.get("/health")
def health():
    healthy, checks = evaluate_health()
    body = {
        "status": "healthy" if healthy else "unhealthy",
        "checks": checks,
        "version": config.APP_VERSION,
        "uptime_seconds": round(time.time() - _started, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return JSONResponse(status_code=200 if healthy else 503, content=body)


@app.get("/users")
def users(_: str = Depends(verify_api_key)):
    return {"count": 4, "data": db.fetch_all("SELECT * FROM users")}


@app.get("/products")
def products(_: str = Depends(verify_api_key)):
    return {"count": 4, "data": db.fetch_all("SELECT * FROM products")}


@app.get("/simulate-error")
def simulate_error(kind: str = "database"):
    """Always fails with an unhandled exception -> HTTP 500. kind = database | zero | key"""
    if kind == "zero":
        return 1 / 0
    if kind == "key":
        return {}["missing_key"]
    raise RuntimeError("Simulated failure: could not acquire connection from database pool (pool exhausted, 20/20 in use)")


@app.get("/simulate-timeout")
async def simulate_timeout(delay: float = 5.0):
    """Sleeps for `delay` seconds (max 60) to simulate a slow dependency."""
    delay = max(0.0, min(delay, 60.0))
    await asyncio.sleep(delay)
    return {"status": "ok", "delayed_by_seconds": delay}


@app.get("/simulate-rate-limit")
def simulate_rate_limit(request: Request):
    """Allows RATE_LIMIT_MAX requests per RATE_LIMIT_WINDOW seconds per client, then returns HTTP 429."""
    client = request.client.host if request.client else "unknown"
    allowed, remaining, retry_after = ratelimit.hit(client)
    if not allowed:
        record_failure(
            "rate_limit",
            request_id=request.state.request_id,
            method=request.method,
            path=request.url.path,
            status=429,
            client=client,
            limit=f"{config.RATE_LIMIT_MAX} requests / {config.RATE_LIMIT_WINDOW}s",
            retry_after_seconds=retry_after,
        )
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit_exceeded", "retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )
    return {"status": "ok", "remaining": remaining}


@app.get("/simulate-health-failure")
def simulate_health_failure(enable: bool = True):
    """Forces /health to return 503 (enable=true) or restores it (enable=false)."""
    _state["forced_unhealthy"] = enable
    healthy, checks = evaluate_health()
    return {"forced_unhealthy": enable, "healthy": healthy, "checks": checks}


@app.get("/errors/recent")
def recent_errors(category: str | None = None, limit: int = 20, _: str = Depends(verify_api_key)):
    """Root-cause data: the most recent classified failures (newest first). Requires X-API-Key."""
    items = [e for e in RECENT if category is None or e["category"] == category]
    return {"count": len(items[:limit]), "failures": items[:limit]}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
