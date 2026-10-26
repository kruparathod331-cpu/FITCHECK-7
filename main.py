import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure current and parent directories are in sys.path for direct execution
app_dir = Path(__file__).resolve().parent
backend_dir = app_dir.parent
workspace_dir = backend_dir.parent
for path in [str(workspace_dir), str(backend_dir), str(app_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from .config import settings
    from .database import init_db
    from .routers import auth, resumes, matcher, reports
except (ImportError, ValueError):
    from app.config import settings
    from app.database import init_db
    from app.routers import auth, resumes, matcher, reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fitcheck.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FitCheck Database...")
    try:
        init_db()
        logger.info("FitCheck Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield
    logger.info("FitCheck Backend shutting down.")

app = FastAPI(
    title="FitCheck API - ATS Resume Optimizer",
    description="Full-stack ATS resume builder, PDF extractor, and explainable job-description matcher for students & early-career job seekers.",
    version="1.0.0",
    lifespan=lifespan
)

# Setup CORS for Next.js frontend, local development, GitHub Pages, and Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?|https://.*\.github\.io|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify backend logs or try again."}
    )

# Include API Routers
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(matcher.router)
app.include_router(reports.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FitCheck API",
        "version": "1.0.0"
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to FitCheck API",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

def main():
    import uvicorn
    logger.info("Starting FitCheck API Server on http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
