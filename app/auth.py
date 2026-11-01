"""API-key authentication dependency."""
from fastapi import Header, HTTPException, Request

from . import config
from .failures import record_failure


def verify_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> str:
    if x_api_key is None or x_api_key not in config.API_KEYS:
        reason = "missing_api_key" if x_api_key is None else "invalid_api_key"
        record_failure(
            "authentication",
            request_id=getattr(request.state, "request_id", None),
            method=request.method,
            path=request.url.path,
            status=401,
            reason=reason,
            client=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=401,
            detail={"error": reason, "message": "Authentication failed: provide a valid X-API-Key header."},
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key
