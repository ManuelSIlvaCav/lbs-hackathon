import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from logger import load_logger
from utils import open_ai_singleton


# Load environment variables
load_dotenv()
load_logger("app")

# Create a logger instance
logger = logging.getLogger("app")

# Import modules after logging configuration is set up
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db_manager
from domains.candidates.routes import router as candidates_router
from domains.job_listings.routes import router as job_listings_router
from domains.companies.routes import router as companies_router
from domains.auth.routes import router as auth_router
from migrations.migrate_company_id_to_objectid import migrate_company_id_to_objectid


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting application...", extra={"context": "lifespan"})
    db_manager.connect()
    """ TODO : Remove this migration after running once """
    migrate_company_id_to_objectid()
    yield
    # Shutdown
    logger.info("🛑 Shutting down application...", extra={"context": "lifespan"})


app = FastAPI(
    title="LBS Hackathon API",
    description="FastAPI server for LBS Hackathon project",
    version="0.1.0",
    lifespan=lifespan,
)


intantiate_openai = open_ai_singleton.OpenAISingleton()


origins = ["http://localhost:3000", "http://localhost:3001", "*"]

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(candidates_router)
app.include_router(job_listings_router)
app.include_router(companies_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LBS Hackathon API",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": os.getenv("MONGODB_DATABASE", "lbs_hackathon"),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    is_connected = db_manager.is_connected()
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "mongodb": "connected" if is_connected else "disconnected",
    }
