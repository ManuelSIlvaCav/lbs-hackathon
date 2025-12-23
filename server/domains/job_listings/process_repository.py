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

        self.collection.create_index(
            "parent_instance_id",
            name="parent_instance_id_index",
            sparse=True,
        )

    def acquire_lock(
        self,
        task_name: str,
        task_instance_id: Optional[str] = None,
        parent_instance_id: Optional[str] = None,
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
                "parent_instance_id": parent_instance_id,
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

    def get_child_tasks(self, parent_instance_id: str) -> list[JobProcessModel]:
        """
        Get all child tasks for a given parent instance ID

        Args:
            parent_instance_id: The parent task instance ID

        Returns:
            List of JobProcessModel objects
        """
        try:
            processes = self.collection.find({"parent_instance_id": parent_instance_id})

            return [JobProcessModel(**process) for process in processes]

        except Exception as e:
            logger.error(
                f"Error getting child tasks: {str(e)}",
                extra={
                    "context": "get_child_tasks",
                    "parent_instance_id": parent_instance_id,
                    "error": str(e),
                },
            )
            return []


# Singleton instance
job_process_repository = JobProcessRepository()
