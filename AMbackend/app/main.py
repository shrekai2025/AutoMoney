"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")

    # Initialize Firebase
    try:
        from app.core.firebase import initialize_firebase
        initialize_firebase()
        print("✓ Firebase initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Firebase initialization failed: {e}")
        print("  App will continue but authentication may not work properly")

    # Start Strategy Scheduler
    try:
        from app.services.strategy.scheduler import strategy_scheduler
        await strategy_scheduler.start()
        print("✓ Strategy scheduler started successfully")
    except Exception as e:
        print(f"⚠ Warning: Strategy scheduler initialization failed: {e}")
        print("  App will continue but automated trading will not work")

    yield

    # Shutdown
    print("Shutting down application...")

    # Stop Strategy Scheduler
    try:
        from app.services.strategy.scheduler import strategy_scheduler
        strategy_scheduler.stop()
        print("✓ Strategy scheduler stopped")
    except Exception as e:
        print(f"⚠ Warning: Strategy scheduler shutdown failed: {e}")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AutoMoney AI Trading System Backend",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )

    # Include API routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return JSONResponse(
            content={
                "status": "healthy",
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
            }
        )

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


# Create app instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
