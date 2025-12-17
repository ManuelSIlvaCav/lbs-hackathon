"""
Tasks domain - centralized location for all Celery tasks

This domain contains all background tasks (Celery) and their related routes.
"""

from .routes import router

__all__ = ["router"]
