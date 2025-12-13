"""
Migration script to convert company_id from string to ObjectId in job_listings collection

This migration:
1. Finds all job_listings documents where company_id is a string
2. Converts valid ObjectId strings to ObjectId type
3. Removes invalid company_id values (non-ObjectId strings)
4. Reports progress and statistics

Usage:
    python server/migrations/migrate_company_id_to_objectid.py
"""

import sys
from pathlib import Path

# Add server directory to path
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

from bson import ObjectId
from bson.errors import InvalidId
from database import get_collection


def is_valid_objectid(value: str) -> bool:
    """Check if a string is a valid ObjectId"""
    try:
        ObjectId(value)
        return True
    except (InvalidId, TypeError):
        return False


def migrate_company_id_to_objectid():
    """
    Migrate company_id field from string to ObjectId in job_listings collection
    """
    print("=" * 80)
    print("Migration: Convert company_id from string to ObjectId")
    print("=" * 80)

    collection = get_collection("job_listings")

    # Statistics
    total_docs = 0
    converted_count = 0
    already_objectid_count = 0
    invalid_count = 0
    no_company_id_count = 0
    error_count = 0

    print("\n1. Analyzing job_listings collection...")

    # Get all documents
    cursor = collection.find({})
    total_docs = collection.count_documents({})

    print(f"   Total documents: {total_docs}")

    if total_docs == 0:
        print("\n✓ No documents to migrate.")
        return

    print("\n2. Processing documents...")

    updates = []
    removals = []

    for doc in cursor:
        doc_id = doc["_id"]
        company_id = doc.get("company_id")

        if company_id is None:
            no_company_id_count += 1
            continue

        # Check if already ObjectId
        if isinstance(company_id, ObjectId):
            already_objectid_count += 1
            continue

        # Check if it's a string
        if isinstance(company_id, str):
            if is_valid_objectid(company_id):
                # Valid ObjectId string - convert it
                updates.append({"_id": doc_id, "company_id": ObjectId(company_id)})
                converted_count += 1
            else:
                # Invalid ObjectId string - remove it
                removals.append(doc_id)
                invalid_count += 1
                print(f"   ⚠ Invalid company_id in document {doc_id}: {company_id}")
        else:
            # Unexpected type - remove it
            removals.append(doc_id)
            invalid_count += 1
            print(
                f"   ⚠ Unexpected company_id type in document {doc_id}: {type(company_id)}"
            )

    print(f"\n3. Migration summary:")
    print(f"   - Total documents: {total_docs}")
    print(f"   - Already ObjectId: {already_objectid_count}")
    print(f"   - To convert: {converted_count}")
    print(f"   - Invalid (will remove): {invalid_count}")
    print(f"   - No company_id: {no_company_id_count}")

    if converted_count == 0 and invalid_count == 0:
        print("\n✓ No migration needed. All company_id fields are already ObjectId.")
        return

    # Confirm before proceeding
    print("\n4. Applying changes...")

    # Apply updates (convert strings to ObjectId)
    if updates:
        print(f"\n   Converting {len(updates)} company_id fields to ObjectId...")
        try:
            for update in updates:
                result = collection.update_one(
                    {"_id": update["_id"]},
                    {"$set": {"company_id": update["company_id"]}},
                )
                if result.modified_count == 0:
                    print(f"   ⚠ Failed to update document {update['_id']}")
                    error_count += 1
        except Exception as e:
            print(f"   ✗ Error during conversion: {e}")
            error_count += len(updates)

    # Remove invalid company_id fields
    if removals:
        print(f"\n   Removing {len(removals)} invalid company_id fields...")
        try:
            result = collection.update_many(
                {"_id": {"$in": removals}}, {"$unset": {"company_id": ""}}
            )
            print(f"   Removed company_id from {result.modified_count} documents")
        except Exception as e:
            print(f"   ✗ Error during removal: {e}")
            error_count += len(removals)

    # Final statistics
    print("\n" + "=" * 80)
    print("Migration completed!")
    print("=" * 80)
    print(f"Successfully converted: {converted_count - error_count}/{converted_count}")
    print(f"Successfully removed invalid: {invalid_count}/{invalid_count}")

    if error_count > 0:
        print(f"\n⚠ Errors encountered: {error_count}")
    else:
        print("\n✓ Migration completed successfully!")

    # Verify migration
    print("\n5. Verifying migration...")
    string_company_ids = collection.count_documents({"company_id": {"$type": "string"}})
    objectid_company_ids = collection.count_documents(
        {"company_id": {"$type": "objectId"}}
    )

    print(f"   Documents with string company_id: {string_company_ids}")
    print(f"   Documents with ObjectId company_id: {objectid_company_ids}")

    if string_company_ids > 0:
        print("\n⚠ Warning: Some company_id fields are still strings!")
    else:
        print("\n✓ All company_id fields are now ObjectId or null!")
