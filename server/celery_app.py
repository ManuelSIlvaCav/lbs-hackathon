"""
Celery application configuration for background task processing
"""

import logging
import os
import sys
from pathlib import Path
from celery import Celery
from dotenv import load_dotenv
from logger import load_logger

# Optional: Define periodic tasks (Celery Beat)
from celery.schedules import crontab

from utils import open_ai_singleton


# Add the current directory to Python path to ensure modules can be imported
# This is especially important for Celery workers
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Load environment variables
load_dotenv()
load_logger("app")

# Create a logger instance
logger = logging.getLogger("app")

# Get Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = os.getenv("REDIS_DB", "0")

# Build Redis URL
try:
    if REDIS_PASSWORD:
        CELERY_BROKER_URL = (
            f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        )
        CELERY_RESULT_BACKEND = (
            f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        )
    else:
        CELERY_BROKER_URL = os.getenv(
            "CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        )
        CELERY_RESULT_BACKEND = os.getenv(
            "CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        )

    # Validate URLs have proper format
    if not CELERY_BROKER_URL.startswith(
        ("redis://", "rediss://", "amqp://", "amqps://")
    ):
        raise ValueError(
            f"Invalid CELERY_BROKER_URL format: '{CELERY_BROKER_URL}'. "
            "Must start with 'redis://', 'rediss://', 'amqp://', or 'amqps://'. "
            "Check your .env file or environment variables."
        )

    if not CELERY_RESULT_BACKEND.startswith(("redis://", "rediss://", "rpc://", "db+")):
        raise ValueError(
            f"Invalid CELERY_RESULT_BACKEND format: '{CELERY_RESULT_BACKEND}'. "
            "Must start with 'redis://', 'rediss://', 'rpc://', or 'db+'. "
            "Check your .env file or environment variables."
        )

    logger.info(
        "Redis configuration loaded successfully",
        extra={
            "context": "celery_app",
            "broker": (
                CELERY_BROKER_URL.split("@")[-1]
                if "@" in CELERY_BROKER_URL
                else CELERY_BROKER_URL
            ),
            "backend": (
                CELERY_RESULT_BACKEND.split("@")[-1]
                if "@" in CELERY_RESULT_BACKEND
                else CELERY_RESULT_BACKEND
            ),
        },
    )

except ValueError as e:
    logger.error(
        f"Configuration error: {e}",
        extra={
            "context": "celery_app",
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT,
        },
    )
    raise
except Exception as e:
    logger.error(
        f"Unexpected error loading Redis configuration: {e}",
        extra={"context": "celery_app"},
        exc_info=True,
    )
    raise

# Create Celery app
try:
    celery_app = Celery(
        "lbs_hackathon",
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
    )
    logger.info("Celery app created successfully", extra={"context": "celery_app"})
except Exception as e:
    logger.error(
        f"Failed to create Celery app: {e}",
        extra={"context": "celery_app"},
        exc_info=True,
    )
    raise
    raise

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60,  # 60 minutes hard limit
    task_soft_time_limit=45 * 60,  # 45 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # Results expire after 1 hour
)

# Auto-discover tasks from all domains
# This will look for tasks.py files in each domain directory
celery_app.autodiscover_tasks(
    [
        "domains.candidates",
        "domains.job_listings",
        "domains.companies",
        "domains.auth",
        "domains.tasks.c_tasks",  # Centralized tasks location
        # Add more domains here as needed
    ]
)

celery_app.conf.beat_schedule = {
    # Refresh job listings for followed companies daily at 5 AM London time
    # Uncomment to enable scheduled execution
    # "refresh-followed-companies-job-listings": {
    #     "task": "domains.companies.tasks.refresh_companies_job_listings",
    #     "schedule": crontab(hour=5, minute=0),  # 5:00 AM UTC (London time in winter)
    #     # Note: For British Summer Time (UTC+1), use hour=4 instead
    #     # Or set timezone="Europe/London" and use hour=5
    # },
    # Enrich job listings for followed companies daily at 6 AM London time
    # Runs after refresh task to enrich newly fetched listings
    # Uncomment to enable scheduled execution
    # "enrich-followed-companies-job-listings": {
    #     "task": "domains.companies.tasks.enrich_all_job_listings",
    #     "schedule": crontab(hour=6, minute=0),  # 6:00 AM UTC (London time in winter)
    #     # Note: For British Summer Time (UTC+1), use hour=5 instead
    #     # Or set timezone="Europe/London" and use hour=6
    # },
    # "revise-enriched-job-listings": {
    #     "task": "domains.job_listings.tasks.revise_enriched_job_listings",
    #     "schedule": 5 * 60,  # Every 5 minutes
    # },
}


intantiate_openai = open_ai_singleton.OpenAISingleton()
logger.info("Celery app initialized", extra={"context": "celery_app"})
