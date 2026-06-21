"""
Sprint Whisperer Backend Application

FastAPI application setup and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.core.config import settings
from app.api.models import ApiResponse
from app.api.routes import upload_router
from app.api.routes import phase2
from app.api.routes import export as export_router
from app.api.routes import forecast
from app.api.routes import demo
from app.api.routes import monte_carlo
from app.api.routes import recommendations
from app.api.routes import risk
from app.api.routes import scope_change


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Sprint Whisperer",
        description="AI-Powered Sprint Forecasting & Recovery Platform",
        version="2.0.0",
    )
    
    # ─── Middleware ──────────────────────────────────────────────────────────
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict to frontend URL in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ─── Routes ──────────────────────────────────────────────────────────────
    
    # Health check
    @app.get("/api/health")
    def health():
        """Health check endpoint."""
        return ApiResponse(
            success=True,
            message="Service is healthy",
            data={
                "status": "ok",
                "version": "2.0.0",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    
    # Register routers
    app.include_router(upload_router, prefix="/api", tags=["Upload"])
    app.include_router(phase2.router)
    app.include_router(export_router.router)
    app.include_router(forecast.router)
    app.include_router(monte_carlo.router)
    app.include_router(recommendations.router)
    app.include_router(risk.router)
    app.include_router(scope_change.router)
    app.include_router(demo.router)
    
    return app


# Create app instance
app = create_app()
