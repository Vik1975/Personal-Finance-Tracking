"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, uploads, transactions, categories, accounts, budgets, analytics, websocket, export

# Initialize Sentry
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        environment="production" if not settings.DEBUG else "development",
    )

app = FastAPI(
    title="Personal Finance Tracker",
    version="0.1.0",
    description="API for document-based expense tracking with OCR and analytics",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(accounts.router)
app.include_router(budgets.router)
app.include_router(analytics.router)
app.include_router(websocket.router)
app.include_router(export.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/version")
async def version():
    """Version endpoint."""
    return {"version": "0.1.0", "service": "Personal Finance Tracker"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Personal Finance Tracker API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
