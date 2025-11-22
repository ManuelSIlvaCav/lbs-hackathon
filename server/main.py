import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import db_manager
from routes.candidates import router as candidates_router
from routes.job_listings import router as job_listings_router
from routes.applications import router as applications_router
from routes.automation import router as automation_router

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("🚀 Starting application...")
    db_manager.connect()
    yield
    # Shutdown
    print("🛑 Shutting down application...")
    db_manager.close()


app = FastAPI(
    title="LBS Hackathon API",
    description="FastAPI server for LBS Hackathon project",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(candidates_router)
app.include_router(job_listings_router)
app.include_router(applications_router)
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
