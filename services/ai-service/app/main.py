"""
NEURAXIS AI Service - Main Application Entry Point
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    cdss,
    diagnostic,
    documentation,
    drug_interaction,
    image_analysis,
    research,
    treatment,
    workflow,
)
from app.api.v1 import router as api_v1_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"📝 Environment: {settings.ENVIRONMENT}")

    # Initialize services here (database, redis, ML models, etc.)

    yield

    # Shutdown
    print(f"👋 Shutting down {settings.APP_NAME}")
    # Cleanup resources here


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-Powered Medical Diagnosis Platform API",
        version=settings.VERSION,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(api_v1_router, prefix="/api/v1")

    # Include Agent Routers (Real Implementation)
    app.include_router(diagnostic.router, prefix="/api/v1")  # /api/v1/diagnose
    app.include_router(research.router, prefix="/api/v1/research")
    app.include_router(treatment.router, prefix="/api/v1/treatment-plan")
    app.include_router(drug_interaction.router, prefix="/api/v1/safety")
    app.include_router(image_analysis.router, prefix="/api/v1/image-analysis")
    app.include_router(documentation.router, prefix="/api/v1/documentation")
    app.include_router(workflow.router, prefix="/api/v1/workflow")

    return app


app = create_application()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": settings.VERSION,
            "service": settings.APP_NAME,
        }
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
    }
