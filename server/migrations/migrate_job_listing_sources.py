"""
Migration script to:
1. Populate JobListingSourceModel for existing job_listings
2. Remove provider, provider_job_id, job_enrichment_id fields from job_listings collection

This migration should be run once to move provider tracking data from job_listings
to the new job_listings_source collection.
"""

import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId

# Add server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_collection
from domains.job_listings.source_models import ProviderSourceInfo, JobListingSourceModel


def migrate_job_listing_sources():
    """
    Main migration function
    """
    print("Starting migration: job_listing_sources...")

    # Get collections
    job_listings_collection = get_collection("job_listings")
    job_listings_source_collection = get_collection("job_listings_source")

    # Create indexes for job_listings_source if they don't exist
    job_listings_source_collection.create_index("job_listing_id", unique=True)
    job_listings_source_collection.create_index("company_id")
    print("✓ Created indexes for job_listings_source collection")

    # Step 1: Find all job listings with provider information
    job_listings = list(
        job_listings_collection.find(
            {
                "$or": [
                    {"provider": {"$exists": True}},
                    {"provider_job_id": {"$exists": True}},
                    {"job_enrichment_id": {"$exists": True}},
                ]
            }
        )
    )

    print(f"Found {len(job_listings)} job listings with provider information")

    if not job_listings:
        print("No job listings to migrate. Exiting.")
        return

    # Step 2: Create job_listings_source documents
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for job in job_listings:
        try:
            job_listing_id = str(job["_id"])
            company_id = job.get("company_id")
            provider = job.get("provider", "manual")
            provider_job_id = job.get("provider_job_id")
            job_enrichment_id = job.get("job_enrichment_id")

            # Skip if no company_id (required for source tracking)
            if not company_id:
                print(f"  ⚠ Skipping job {job_listing_id}: no company_id")
                skipped_count += 1
                continue

            # Skip if no provider information at all
            if not provider and not provider_job_id and not job_enrichment_id:
                print(f"  ⚠ Skipping job {job_listing_id}: no provider information")
                skipped_count += 1
                continue

            # Check if source already exists
            existing_source = job_listings_source_collection.find_one(
                {"job_listing_id": job_listing_id}
            )

            if existing_source:
                print(f"  ⚠ Skipping job {job_listing_id}: source already exists")
                skipped_count += 1
                continue

            # Create provider source info
            provider_info = ProviderSourceInfo(
                job_enrichment_id=job_enrichment_id,
                provider_job_id=provider_job_id
                or job_listing_id,  # Use job_listing_id as fallback
                url=job.get("url"),
                first_seen_at=job.get("created_at", datetime.now()),
                last_seen_at=job.get("last_seen_at")
                or job.get("updated_at", datetime.now()),
            )

            # Create source tracking document
            source_model = JobListingSourceModel(
                job_listing_id=job_listing_id,
                company_id=company_id,
                sources={provider: provider_info},
                created_at=job.get("created_at", datetime.now()),
                updated_at=datetime.now(),
            )

            # Insert into job_listings_source
            source_dict = source_model.model_dump(by_alias=True, exclude=["id"])
            # Convert ProviderSourceInfo to dict
            source_dict["sources"][provider] = provider_info.model_dump()

            job_listings_source_collection.insert_one(source_dict)

            print(f"  ✓ Migrated job {job_listing_id} with provider '{provider}'")
            migrated_count += 1

        except Exception as e:
            print(f"  ✗ Error migrating job {job.get('_id')}: {e}")
            error_count += 1

    print(f"\n--- Migration Summary (Step 1) ---")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")

    # Step 3: Remove provider fields from job_listings collection
    print("\n--- Step 2: Removing provider fields from job_listings ---")

    try:
        result = job_listings_collection.update_many(
            {},
            {
                "$unset": {
                    "provider": "",
                    "provider_job_id": "",
                    "job_enrichment_id": "",
                }
            },
        )

        print(f"✓ Removed provider fields from {result.modified_count} job listings")

    except Exception as e:
        print(f"✗ Error removing provider fields: {e}")

    # Step 4: Remove indexes on provider fields (they no longer exist)
    print("\n--- Step 3: Updating indexes ---")
    try:
        # Get existing indexes
        existing_indexes = list(job_listings_collection.list_indexes())
        index_names = [idx["name"] for idx in existing_indexes]

        # Drop old provider-related indexes if they exist
        indexes_to_drop = ["provider_job_id_1", "job_enrichment_id_1"]
        for index_name in indexes_to_drop:
            if index_name in index_names:
                job_listings_collection.drop_index(index_name)
                print(f"  ✓ Dropped index: {index_name}")

        # Keep company_id and last_seen_at indexes as they're still used
        print("  ✓ Kept company_id and last_seen_at indexes")

    except Exception as e:
        print(f"  ⚠ Warning updating indexes: {e}")

    print("\n=== Migration Complete ===")
    print(f"Total documents migrated: {migrated_count}")
    print(f"Provider fields removed from job_listings collection")
    print(f"All provider tracking now in job_listings_source collection")


def rollback_migration():
    """
    Rollback function to reverse the migration if needed
    WARNING: This will copy data back from job_listings_source to job_listings
    """
    print("Starting rollback: job_listing_sources...")

    # Get collections
    job_listings_collection = get_collection("job_listings")
    job_listings_source_collection = get_collection("job_listings_source")

    # Get all source documents
    sources = list(job_listings_source_collection.find({}))
    print(f"Found {len(sources)} source documents to rollback")

    rollback_count = 0
    error_count = 0

    for source in sources:
        try:
            job_listing_id = source["job_listing_id"]
            sources_dict = source.get("sources", {})

            # Get the first provider (most common case)
            if sources_dict:
                provider_name = list(sources_dict.keys())[0]
                provider_info = sources_dict[provider_name]

                # Update job listing with provider fields
                job_listings_collection.update_one(
                    {"_id": ObjectId(job_listing_id)},
                    {
                        "$set": {
                            "provider": provider_name,
                            "provider_job_id": provider_info.get("provider_job_id"),
                            "job_enrichment_id": provider_info.get("job_enrichment_id"),
                        }
                    },
                )

                print(f"  ✓ Restored provider fields for job {job_listing_id}")
                rollback_count += 1

        except Exception as e:
            print(f"  ✗ Error rolling back job {source.get('job_listing_id')}: {e}")
            error_count += 1

    print(f"\n--- Rollback Summary ---")
    print(f"Successfully rolled back: {rollback_count}")
    print(f"Errors: {error_count}")
    print(f"\nNote: Source documents still exist in job_listings_source collection")
    print(f"Manually delete them if you want to completely reverse the migration")
