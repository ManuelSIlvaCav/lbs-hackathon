"""
Script to create a unique compound index on applications collection
to prevent duplicate applications (same candidate + job + status)
"""

from pymongo import ASCENDING
from database import db_manager


def create_unique_application_index():
    """
    Create a unique compound index on the applications collection
    to ensure a candidate cannot have multiple applications to the same
    job listing with the same status.
    """
    try:
        # Get the applications collection
        db = db_manager.get_database()
        applications_collection = db["applications"]

        # Create unique compound index on candidate_id + job_listing_id + status
        # This prevents duplicate applications with the same status
        index_name = applications_collection.create_index(
            [
                ("candidate_id", ASCENDING),
                ("job_listing_id", ASCENDING),
                ("status", ASCENDING),
            ],
            unique=True,
            name="unique_candidate_job_status",
            background=True,  # Create index in background to avoid blocking
        )

        print(f"✓ Successfully created unique index: {index_name}")
        print("  This ensures a candidate cannot have duplicate applications")
        print("  to the same job listing with the same status.")

        # List all indexes to verify
        print("\nCurrent indexes on applications collection:")
        for index in applications_collection.list_indexes():
            print(f"  - {index['name']}: {index.get('key', {})}")
            if index.get("unique"):
                print(f"    (unique constraint)")

    except Exception as e:
        print(f"✗ Error creating index: {e}")
        print("\nNote: If you see a 'duplicate key error', it means there are")
        print("already duplicate applications in your database. You'll need to")
        print("clean those up before creating the unique index.")


if __name__ == "__main__":
    print("Creating unique index on applications collection...\n")
    create_unique_application_index()
    print("\n✓ Index creation complete!")
