"""
Main FastAPI application for ECE 461 Phase 2
Trustworthy Model Registry API
"""
import logging
import sys

# Setup basic logging FIRST so we can see import errors
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
logger.info("=== Starting Lambda initialization ===")

try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import time
    import os
    logger.info("Core imports successful")

    from .config import settings
    logger.info(f"Config loaded - use_mock_db={settings.use_mock_db}")
    
    from .routes import health, artifacts, auth, tracks, rating, cost, lineage, license_check
    logger.info("All route imports successful")
except Exception as e:
    logger.error(f"Import error: {str(e)}", exc_info=True)
    raise

# Setup logging
logger.info("Setting up logging configuration")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for ECE 461/Fall 2025/Project Phase 2: A Trustworthy Model Registry",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Time: {process_time:.3f}s")
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
# IMPORTANT: Rating router must be included BEFORE artifacts router
# because /artifacts/{id}/rate must match before /artifacts/{artifact_type}/{id}
app.include_router(health.router, tags=["Health"])
app.include_router(rating.router, tags=["Rating"])
app.include_router(artifacts.router, tags=["Artifacts"])
app.include_router(cost.router, tags=["Cost"])
app.include_router(lineage.router, tags=["Lineage"])
app.include_router(license_check.router, tags=["License"])
app.include_router(auth.router, tags=["Authentication"])
app.include_router(tracks.router, tags=["Tracks"])


# Mount static files and serve frontend
# Get the directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Frontend is one level up from api/ directory
FRONTEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "frontend")

if os.path.exists(FRONTEND_DIR):
    # Mount static files (CSS, JS, images)
    static_dir = os.path.join(FRONTEND_DIR, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Serve index.html at /ui
    @app.get("/ui")
    async def serve_frontend():
        """Serve the frontend interface"""
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not found"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "ui": "/ui"
    }


# Lambda handler
from mangum import Mangum
handler = Mangum(app, lifespan="off")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug
    )
