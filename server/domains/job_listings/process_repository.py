"""
Repository for job process tracking and locking
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from database import get_collection
from domains.job_listings.process_models import (
    JobProcessModel,
    JobProcessStatus,
)

logger = logging.getLogger("app")


class JobProcessRepository:
    """Repository for managing job process locks and tracking"""

    def __init__(self):

        self.collection: Collection = get_collection("job_processes")

        # Create unique index on task_name where status is 'processing'
        # This ensures only one instance of a task runs at a time
        # Completed/failed tasks can coexist with same task_name
        self.collection.create_index(
            {"task_name": 1, "status": 1},
            unique=True,
            name="task_name_status_unique_lock",
        )

        # Create TTL index to auto-cleanup old completed processes after 7 days
        self.collection.create_index(
            "completed_at",
            expireAfterSeconds=604800,  # 7 days
            name="completed_at_ttl",
        )

    def acquire_lock(
        self, task_name: str, task_instance_id: Optional[str] = None
    ) -> Optional[JobProcessModel]:
        """
        Attempt to acquire a processing lock for a task

        Args:
            task_name: Name of the task (e.g., 'revise_enriched_job_listings')
            task_instance_id: Optional Celery task ID for tracking

        Returns:
            JobProcessModel if lock acquired, None if already locked
        """
        try:
            process_data = {
                "task_name": task_name,
                "task_instance_id": task_instance_id,
                "status": JobProcessStatus.PROCESSING,
                "started_at": datetime.now(),
                "retry_count": 0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            result = self.collection.insert_one(process_data)

            if result.inserted_id:
                process_data["_id"] = result.inserted_id
                logger.info(
                    f"Acquired lock for task {task_name}",
                    extra={
                        "context": "acquire_lock",
                        "task_name": task_name,
                        "task_instance_id": task_instance_id,
                    },
                )
                return JobProcessModel(**process_data)

        except DuplicateKeyError as e:
            logger.info(
                "Lock already exists for task ",
                extra={
                    "context": "acquire_lock",
                    "task_name": task_name,
                    "task_instance_id": task_instance_id,
                    "error_msg": str(e),
                },
            )
            return None

        except Exception as e:
            logger.error(
                f"Error acquiring lock: {str(e)}",
                extra={
                    "context": "acquire_lock",
                    "task_name": task_name,
                    "error": str(e),
                },
            )
            return None

    def release_lock(
        self,
        task_name: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Release a processing lock by deleting it

        Args:
            task_name: Name of the task
            status: Final status (completed, failed, released) - kept for API compatibility but not used
            error_message: Optional error message if failed - kept for API compatibility but not used

        Returns:
            True if lock released, False otherwise
        """
        try:
            result = self.collection.delete_one(
                {
                    "task_name": task_name,
                    "status": JobProcessStatus.PROCESSING,  # Only delete processing locks
                }
            )

            if result.deleted_count > 0:
                logger.info(
                    f"Released lock for task {task_name}",
                    extra={
                        "context": "release_lock",
                        "task_name": task_name,
                        "error_message": error_message if error_message else None,
                    },
                )
                return True

            logger.warning(
                f"No processing lock found to release for task {task_name}",
                extra={
                    "context": "release_lock",
                    "task_name": task_name,
                },
            )
            return False

        except Exception as e:
            logger.error(
                f"Error releasing lock: {str(e)}",
                extra={
                    "context": "release_lock",
                    "task_name": task_name,
                    "error": str(e),
                },
            )
            return False

    def get_lock_status(self, task_name: str) -> Optional[JobProcessModel]:
        """
        Get the current lock status for a task

        Args:
            task_name: Name of the task

        Returns:
            JobProcessModel if lock exists, None otherwise
        """
        try:
            process = self.collection.find_one({"task_name": task_name})

            if process:
                return JobProcessModel(**process)

            return None

        except Exception as e:
            logger.error(
                f"Error getting lock status: {str(e)}",
                extra={
                    "context": "get_lock_status",
                    "task_name": task_name,
                    "error": str(e),
                },
            )
            return None

    def cleanup_stale_locks(self, hours: int = 2) -> int:
        """
        Clean up locks that have been processing for too long
        (likely due to crashes or hanging processes)

        Args:
            hours: Number of hours after which a lock is considered stale

        Returns:
            Number of stale locks cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            result = self.collection.update_many(
                {
                    "status": JobProcessStatus.PROCESSING,
                    "started_at": {"$lt": cutoff_time},
                },
                {
                    "$set": {
                        "status": JobProcessStatus.RELEASED,
                        "completed_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "error_message": f"Stale lock cleaned up after {hours} hours",
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(
                    f"Cleaned up {result.modified_count} stale locks",
                    extra={
                        "context": "cleanup_stale_locks",
                        "count": result.modified_count,
                        "hours": hours,
                    },
                )

            return result.modified_count

        except Exception as e:
            logger.error(
                f"Error cleaning up stale locks: {str(e)}",
                extra={"context": "cleanup_stale_locks", "error": str(e)},
            )
            return 0


# Singleton instance
job_process_repository = JobProcessRepository()
