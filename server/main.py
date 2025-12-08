import json
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging.config import dictConfig
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


# Custom JSON formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


# Define the logging configuration
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": JsonFormatter}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "app": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

dictConfig(log_config)

# Create a logger instance
logger = logging.getLogger("app")

# Import modules after logging configuration is set up
from database import db_manager
from domains.candidates.routes import router as candidates_router
from domains.job_listings.routes import router as job_listings_router
from domains.applications.routes import router as applications_router
from domains.companies.routes import router as companies_router
from domains.auth.routes import router as auth_router
from routes.automation import router as automation_router
from migrations.migrate_job_listing_sources import migrate_job_listing_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting application...")
    db_manager.connect()
    yield
    # Shutdown
    logger.info("🛑 Shutting down application...")


app = FastAPI(
    title="LBS Hackathon API",
    description="FastAPI server for LBS Hackathon project",
    version="0.1.0",
    lifespan=lifespan,
)

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
app.include_router(applications_router)
app.include_router(companies_router)
app.include_router(automation_router)


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
