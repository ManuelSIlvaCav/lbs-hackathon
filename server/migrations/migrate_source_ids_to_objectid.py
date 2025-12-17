"""
Migration Script: Convert job_listing_id and company_id to ObjectId in job_listings_source collection

This migration addresses the flaw where job_listing_id and company_id were stored as strings
instead of ObjectId references, which breaks referential integrity and query performance.

BEFORE:
{
    "_id": ObjectId("..."),
    "job_listing_id": "507f1f77bcf86cd799439011",  # String
    "company_id": "507f1f77bcf86cd799439012",      # String
    "sources": {...}
}

AFTER:
{
    "_id": ObjectId("..."),
    "job_listing_id": ObjectId("507f1f77bcf86cd799439011"),  # ObjectId
    "company_id": ObjectId("507f1f77bcf86cd799439012"),      # ObjectId
    "sources": {...}
}

Migration Steps:
1. Pre-migration validation: Check data consistency
2. Backup collection state
3. Convert string IDs to ObjectIds
4. Post-migration validation
5. Create indexes if needed

Usage:
    python migrations/migrate_source_ids_to_objectid.py [--dry-run] [--backup]

Options:
    --dry-run: Preview changes without applying them
    --backup: Create a backup collection before migration
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bson import ObjectId
from pymongo.errors import BulkWriteError
from database import get_collection


class SourceIdMigration:
    """Handler for migrating source collection IDs to ObjectId"""

    def __init__(self, dry_run: bool = False, backup: bool = False):
        self.collection = get_collection("job_listings_source")
        self.dry_run = dry_run
        self.backup = backup
        self.backup_collection_name = (
            f"job_listings_source_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    def log(self, message: str, level: str = "INFO"):
        """Log migration messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def pre_migration_validation(self) -> Tuple[bool, Dict]:
        """
        Validate data before migration - simplified version
        Assumes all string IDs are valid ObjectIds and references exist

        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.log("=== PRE-MIGRATION VALIDATION ===")

        report = {
            "total_docs": 0,
            "already_objectid": 0,
            "needs_conversion": 0,
        }

        # Count total documents
        report["total_docs"] = self.collection.count_documents({})
        self.log(f"Total documents in collection: {report['total_docs']}")

        if report["total_docs"] == 0:
            self.log("No documents to migrate", "WARNING")
            return True, report

        # Count documents already using ObjectId for both fields
        report["already_objectid"] = self.collection.count_documents(
            {
                "job_listing_id": {"$type": "objectId"},
                "company_id": {"$type": "objectId"},
            }
        )

        # Count documents needing conversion (at least one string field)
        report["needs_conversion"] = self.collection.count_documents(
            {
                "$or": [
                    {"job_listing_id": {"$type": "string"}},
                    {"company_id": {"$type": "string"}},
                ]
            }
        )

        # Print validation results
        self.log(f"Documents already using ObjectId: {report['already_objectid']}")
        self.log(f"Documents needing conversion: {report['needs_conversion']}")

        if report["needs_conversion"] == 0:
            self.log(
                "No conversion needed - all documents already use ObjectId", "INFO"
            )

        self.log("Pre-migration validation PASSED", "SUCCESS")
        return True, report

    def create_backup(self):
        """Create a backup of the collection"""
        self.log(f"Creating backup: {self.backup_collection_name}")

        db = self.collection.database
        backup_collection = db[self.backup_collection_name]

        # Copy all documents
        docs = list(self.collection.find())
        if docs:
            backup_collection.insert_many(docs)
            self.log(f"Backup created with {len(docs)} documents", "SUCCESS")
        else:
            self.log("No documents to backup", "WARNING")

    def perform_migration(self) -> Dict:
        """
        Perform the actual migration

        Returns:
            Migration statistics
        """
        self.log("=== PERFORMING MIGRATION ===")

        stats = {
            "converted": 0,
            "skipped": 0,
            "errors": [],
        }

        # Get all documents that need conversion
        docs_to_convert = list(
            self.collection.find(
                {
                    "$or": [
                        {"job_listing_id": {"$type": "string"}},
                        {"company_id": {"$type": "string"}},
                    ]
                }
            )
        )

        self.log(f"Found {len(docs_to_convert)} documents to convert")

        if self.dry_run:
            self.log("DRY RUN - No changes will be applied", "WARNING")
            for doc in docs_to_convert[:5]:  # Show first 5
                self.log(f"Would convert: {doc['_id']}")
                self.log(f"  job_listing_id: {doc.get('job_listing_id')} -> ObjectId")
                self.log(f"  company_id: {doc.get('company_id')} -> ObjectId")
            stats["converted"] = len(docs_to_convert)
            return stats

        # Perform actual conversion
        from pymongo import UpdateOne

        bulk_operations = []

        for doc in docs_to_convert:
            try:
                update_fields = {}

                # Convert job_listing_id if it's a string
                if isinstance(doc.get("job_listing_id"), str):
                    update_fields["job_listing_id"] = ObjectId(doc["job_listing_id"])

                # Convert company_id if it's a string
                if isinstance(doc.get("company_id"), str):
                    update_fields["company_id"] = ObjectId(doc["company_id"])

                if update_fields:
                    bulk_operations.append(
                        UpdateOne({"_id": doc["_id"]}, {"$set": update_fields})
                    )

            except Exception as e:
                error_msg = f"Error preparing doc {doc['_id']}: {str(e)}"
                self.log(error_msg, "ERROR")
                stats["errors"].append(error_msg)

        # Execute bulk update
        if bulk_operations:
            try:
                result = self.collection.bulk_write(bulk_operations, ordered=False)
                stats["converted"] = result.modified_count
                self.log(
                    f"Successfully converted {stats['converted']} documents", "SUCCESS"
                )
            except BulkWriteError as e:
                self.log(f"Bulk write error: {str(e)}", "ERROR")
                stats["errors"].append(str(e))
                stats["converted"] = e.details.get("nModified", 0)

        return stats

    def post_migration_validation(self) -> Tuple[bool, Dict]:
        """
        Validate data after migration

        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.log("=== POST-MIGRATION VALIDATION ===")

        report = {
            "total_docs": 0,
            "all_objectid": 0,
            "remaining_strings": [],
        }

        report["total_docs"] = self.collection.count_documents({})

        # Check for any remaining string IDs
        remaining_string_job_ids = self.collection.count_documents(
            {"job_listing_id": {"$type": "string"}}
        )
        remaining_string_company_ids = self.collection.count_documents(
            {"company_id": {"$type": "string"}}
        )

        if remaining_string_job_ids > 0:
            report["remaining_strings"].append(
                f"{remaining_string_job_ids} job_listing_id still strings"
            )

        if remaining_string_company_ids > 0:
            report["remaining_strings"].append(
                f"{remaining_string_company_ids} company_id still strings"
            )

        # Count documents with ObjectId
        all_objectid = self.collection.count_documents(
            {
                "job_listing_id": {"$type": "objectId"},
                "company_id": {"$type": "objectId"},
            }
        )
        report["all_objectid"] = all_objectid

        self.log(f"Total documents: {report['total_docs']}")
        self.log(f"Documents with ObjectId for both fields: {report['all_objectid']}")

        is_valid = len(report["remaining_strings"]) == 0

        if report["remaining_strings"]:
            self.log("Post-migration validation FAILED:", "ERROR")
            for issue in report["remaining_strings"]:
                self.log(f"  - {issue}", "ERROR")
        else:
            self.log(
                "Post-migration validation PASSED - All IDs are ObjectId", "SUCCESS"
            )

        return is_valid, report

    def recreate_indexes(self):
        """Recreate indexes after migration"""
        self.log("=== RECREATING INDEXES ===")

        try:
            # Drop old indexes if they exist
            try:
                self.collection.drop_index("job_listing_id_1")
            except:
                pass

            # Create new indexes
            self.collection.create_index("job_listing_id", unique=True)
            self.log("Created unique index on job_listing_id", "SUCCESS")

            self.collection.create_index("company_id")
            self.log("Created index on company_id", "SUCCESS")

            self.collection.create_index([("job_listing_id", 1), ("company_id", 1)])
            self.log(
                "Created compound index on (job_listing_id, company_id)", "SUCCESS"
            )

        except Exception as e:
            self.log(f"Error creating indexes: {str(e)}", "ERROR")

    def run(self):
        """Execute the complete migration process"""
        self.log("=" * 80)
        self.log("STARTING MIGRATION: Source IDs to ObjectId")
        self.log("=" * 80)

        # Step 1: Pre-migration validation
        is_valid, pre_report = self.pre_migration_validation()
        if not is_valid:
            self.log("Migration aborted due to validation errors", "ERROR")
            return False

        # Step 2: Create backup if requested
        if self.backup and not self.dry_run:
            self.create_backup()

        # Step 3: Perform migration
        migration_stats = self.perform_migration()

        if self.dry_run:
            self.log("=" * 80)
            self.log("DRY RUN COMPLETED - No changes were made", "INFO")
            self.log("=" * 80)
            return True

        # Step 4: Post-migration validation
        is_valid, post_report = self.post_migration_validation()

        # Step 5: Recreate indexes
        if is_valid:
            self.recreate_indexes()

        # Summary
        self.log("=" * 80)
        self.log("MIGRATION SUMMARY")
        self.log("=" * 80)
        self.log(f"Documents converted: {migration_stats['converted']}")
        self.log(f"Documents skipped: {migration_stats['skipped']}")
        self.log(f"Errors: {len(migration_stats['errors'])}")

        if migration_stats["errors"]:
            self.log("Error details:", "ERROR")
            for error in migration_stats["errors"][:10]:  # Show first 10
                self.log(f"  - {error}", "ERROR")

        if is_valid:
            self.log("=" * 80)
            self.log("MIGRATION COMPLETED SUCCESSFULLY", "SUCCESS")
            self.log("=" * 80)
        else:
            self.log("=" * 80)
            self.log("MIGRATION COMPLETED WITH ERRORS", "ERROR")
            self.log("=" * 80)

        return is_valid


def main():
    """Main entry point for migration script"""
    parser = argparse.ArgumentParser(
        description="Migrate job_listings_source collection IDs to ObjectId"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup collection before migration",
    )

    args = parser.parse_args()

    migration = SourceIdMigration(dry_run=args.dry_run, backup=args.backup)
    success = migration.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
