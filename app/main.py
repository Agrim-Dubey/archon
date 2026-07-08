"""FastAPI Application Main Entrypoint and Lifespan."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.exceptions import ArchonException, archon_exception_handler
from app.core.metrics import PrometheusMiddleware
from app.core.ratelimit import RateLimiterMiddleware
from app.core.telemetry import init_telemetry
from app.services.seed_data import seed_database
from app.domains.auth.router import router as auth_router
from app.domains.interview.router import router as interview_router
from app.domains.diagram.router import router as diagram_router
from app.domains.ai.router import router as ai_router
from app.domains.reports.router import router as reports_router
from app.domains.quiz.router import router as quiz_router
from app.domains.analytics.router import router as analytics_router
from app.domains.dashboard.router import router as dashboard_router
from app.domains.settings.router import router as settings_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database, telemetry, and seed defaults."""
    logger.info("Starting Archon FastAPI platform...")
    init_telemetry(settings.PROJECT_NAME)
    await init_db()

    # Seed questions and decks
    async with AsyncSessionLocal() as db:
        await seed_database(db)

    logger.info("Archon platform ready to conduct interviews.")
    yield
    logger.info("Shutting down Archon platform...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.FRONTEND_URLS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # 2. Prometheus Metrics Middleware
    app.add_middleware(PrometheusMiddleware)

    # 3. Rate Limiter Middleware
    app.add_middleware(RateLimiterMiddleware, limit=120, window_seconds=60)

    # 4. Global Exception Handlers
    app.add_exception_handler(ArchonException, archon_exception_handler)

    # 5. Prometheus /metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # 6. Include Domain Routers
    app.include_router(auth_router)
    app.include_router(interview_router)
    app.include_router(diagram_router)
    app.include_router(ai_router)
    app.include_router(reports_router)
    app.include_router(quiz_router)
    app.include_router(analytics_router)
    app.include_router(dashboard_router)
    app.include_router(settings_router)

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": settings.PROJECT_NAME, "version": settings.VERSION}

    return app


app = create_app()
