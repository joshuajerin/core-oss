"""
FastAPI application for Vercel
Vercel auto-detects and deploys FastAPI apps at index.py
NO vercel.json or Mangum needed!
"""
import sys
import os

# Add project root to path so we can import from api/ and lib/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sentry_sdk
import time
import uuid
import logging
import traceback
from contextvars import ContextVar
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from api.config import settings
from api.schemas import HealthResponse, StatusResponse
from lib.supabase_client import start_supabase_request_scope, reset_supabase_request_scope

# Per-request ID for error attribution and debugging
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

logger = logging.getLogger(__name__)


def _sentry_filter_noise(event, hint):
    """Drop expected HTTP errors (4xx) from Sentry to reduce noise."""
    exc = hint.get("exc_info", (None, None, None))[1]
    if isinstance(exc, HTTPException) and exc.status_code < 500:
        return None
    return event


sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.api_env,
    traces_sample_rate=0.05,
    send_default_pii=True,
    before_send=_sentry_filter_noise,
)

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from api.rate_limit import limiter

from api.routers import auth, calendar, email, webhooks, cron, sync, documents, files, chat, chat_attachments, app_drawer, preferences, workspaces, invitations, messages, users, projects, notifications, init, agents, agent_dispatch, permissions, public, workers, builder

# Create FastAPI app - Vercel will auto-detect this
app = FastAPI(
    title=settings.app_name,
    description="FastAPI backend for the all-in-one productivity app",
    version=settings.app_version,
    debug=settings.debug
)

# Rate limiting — middleware runs BEFORE FastAPI validation/dependencies
# Without this, invalid requests (422) bypass the decorator-based limiter
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _get_request_id() -> str | None:
    return _request_id_ctx.get(None)


# HTTP exception handler — wraps all HTTPException responses in the standard envelope
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": _status_to_error_code(exc.status_code),
            "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "request_id": _get_request_id(),
        },
    )


# Validation error handler — wraps 422 responses in the standard envelope
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        {"field": " -> ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    messages = [d["message"] for d in details]
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": ", ".join(messages) if messages else "Validation error",
            "details": details,
            "request_id": _get_request_id(),
        },
    )


# Global exception handler for unhandled exceptions
# This ensures CORS headers are included even on 500 errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler that returns proper JSON error responses.

    This is critical for CORS: when an unhandled exception occurs, FastAPI's
    default error handler may not include CORS headers if the exception happens
    before response headers are sent. By catching all exceptions here and
    returning a proper JSONResponse, we ensure the CORS middleware can add
    its headers to the response.
    """
    # Log the full traceback for debugging
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}\n"
        f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
    )

    # Report to Sentry
    sentry_sdk.capture_exception(exc)

    # Return a proper JSON response (CORS middleware will add headers)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Internal server error",
            "request_id": _get_request_id(),
        }
    )


def _status_to_error_code(status_code: int) -> str:
    """Map HTTP status codes to machine-readable error codes."""
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
    }.get(status_code, f"http_{status_code}")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def supabase_request_scope_middleware(request: Request, call_next):
    scope_token = start_supabase_request_scope()
    try:
        return await call_next(request)
    finally:
        reset_supabase_request_scope(scope_token)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        # Let the global exception handler deal with it, but ensure we don't swallow errors
        raise
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# Request timing + request ID middleware for performance monitoring and debugging
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    # Generate a unique request ID for tracing
    request_id = uuid.uuid4().hex[:16]
    token = _request_id_ctx.set(request_id)
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        # Log timing even for failed requests
        process_time_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"[PERF] {request.method} {request.url.path} - {process_time_ms:.2f}ms - EXCEPTION: {type(exc).__name__} - rid={request_id}"
        )
        raise
    finally:
        _request_id_ctx.reset(token)

    process_time_ms = (time.perf_counter() - start_time) * 1000

    # Add timing and request ID to response headers
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
    response.headers["X-Request-Id"] = request_id

    # Log the request timing
    logger.info(
        f"[PERF] {request.method} {request.url.path} - {process_time_ms:.2f}ms - Status: {response.status_code} - rid={request_id}"
    )

    return response


# Include routers
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(invitations.router)
app.include_router(calendar.router)
app.include_router(email.router)
app.include_router(documents.router)
app.include_router(files.router)
app.include_router(webhooks.router)
app.include_router(cron.router)
app.include_router(sync.router)
app.include_router(chat.router)
app.include_router(chat_attachments.router)
app.include_router(app_drawer.router)
app.include_router(preferences.router)
app.include_router(messages.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(notifications.router)
app.include_router(permissions.router)
app.include_router(agents.router)
app.include_router(agent_dispatch.router)
app.include_router(init.router)
app.include_router(public.router)
app.include_router(workers.router)
app.include_router(builder.router)

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Core Productivity API is running",
        "version": settings.app_version
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "core-api",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
