"""FastAPI application for the Order Intelligence Platform."""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from order_shared.adapters import create_adapters, get_adapters

from order_api.auth import (
    LoginRequest,
    TokenResponse,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
)
from order_api.routers import (
    admin,
    conversations,
    customers,
    emails,
    health,
    orders,
    queues,
    reports,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Order Intelligence Platform API")
    create_adapters()
    logger.info("Adapters initialized")
    yield
    # Shutdown
    logger.info("Shutting down Order Intelligence Platform API")


app = FastAPI(
    title="Order Intelligence Platform",
    version=os.environ.get("APP_VERSION", "0.1.0"),
    lifespan=lifespan,
)

# --- CORS ---
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request timing middleware ---
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    return response


# --- Global exception handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )


# --- Auth endpoint (mounted directly, not in a router) ---
@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(body: LoginRequest):
    """Authenticate with email and password, receive JWT tokens."""
    user = await authenticate_user(body.email, body.password)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "UNAUTHORIZED", "message": "Invalid email or password"}},
        )

    token_data = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# --- Mount Routers ---
app.include_router(health.router)
app.include_router(orders.router)
app.include_router(emails.router)
app.include_router(queues.router)
app.include_router(conversations.router)
app.include_router(customers.router)
app.include_router(reports.router)
app.include_router(admin.router)
