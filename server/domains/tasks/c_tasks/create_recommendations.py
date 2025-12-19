"""
Celery task to create job recommendations for candidates

This task:
1. Gets all candidates with search preferences
2. For each candidate, searches job listings matching their profile_categories and role_titles
3. Creates recommendations for matching jobs
4. Uses bulk operations for efficiency
"""

import logging
from celery import shared_task
from datetime import datetime
from bson import ObjectId

from database import get_collection
from domains.recommendations.repository import RecommendationRepository
from domains.recommendations.models import RecommendationCreate
from domains.job_listings.categories import get_role_titles_by_category

logger = logging.getLogger("app")


@shared_task(name="domains.tasks.c_tasks.create_recommendations")
def create_recommendations():
    """
    Create job recommendations for all candidates based on their search preferences

    This task:
    - Finds all candidates with search preferences (profile_categories and/or role_titles)
    - For each candidate, searches for job listings matching their preferences
    - Creates recommendations for matching jobs that don't already exist
    - Uses bulk operations for performance

    Returns:
        dict: Summary of recommendations created
    """
    logger.info("Starting create_recommendations task")

    candidates_collection = get_collection("candidates")
    job_listings_collection = get_collection("job_listings")
    recommendation_repo = RecommendationRepository()

    # Statistics
    total_candidates = 0
    total_jobs_found = 0
    total_recommendations_created = 0
    errors = []

    try:
        # Get all candidates with search preferences
        candidates = list(
            candidates_collection.find(
                {
                    "$or": [
                        {
                            "search_preferences.profile_categories": {
                                "$exists": True,
                                "$ne": None,
                                "$ne": [],
                            }
                        },
                        {
                            "search_preferences.role_titles": {
                                "$exists": True,
                                "$ne": None,
                                "$ne": [],
                            }
                        },
                    ]
                }
            )
        )

        total_candidates = len(candidates)
        logger.info(f"Found {total_candidates} candidates with search preferences")

        # Process each candidate
        for candidate in candidates:
            try:
                candidate_id = candidate["_id"]
                search_prefs = candidate.get("search_preferences", {})

                profile_categories = search_prefs.get("profile_categories", []) or []
                role_titles = search_prefs.get("role_titles", []) or []
                locations = search_prefs.get("locations", []) or []

                if not profile_categories and not role_titles:
                    continue

                # Build $or conditions for matching
                match_conditions = []

                # Strategy:
                # 1. If candidate has both profile_categories AND role_titles:
                #    - For each category, intersect candidate's role_titles with valid roles for that category
                #    - Only search for jobs with that category AND those specific intersected roles
                # 2. If candidate only has profile_categories (no specific roles):
                #    - Search for jobs with any of those categories and any valid role for that category
                # 3. If candidate only has role_titles (no categories):
                #    - Search for jobs with any of those role_titles

                if profile_categories and role_titles:
                    # Case 1: Both categories and roles specified
                    # For each category, find intersection of candidate's roles with valid roles for that category
                    for category in profile_categories:
                        valid_roles_for_category = get_role_titles_by_category(category)
                        # Intersect candidate's selected roles with valid roles for this category
                        matching_roles = [
                            r for r in role_titles if r in valid_roles_for_category
                        ]

                        if matching_roles:
                            # Add condition: category matches AND role is in candidate's selected roles (that are valid for this category)
                            match_conditions.append(
                                {
                                    "$and": [
                                        {"profile_categories": category},
                                        {"role_titles": {"$in": matching_roles}},
                                    ]
                                }
                            )

                elif profile_categories and not role_titles:
                    # Case 2: Only categories specified, no specific roles
                    # Match any job with these categories and any valid role
                    for category in profile_categories:
                        valid_roles_for_category = get_role_titles_by_category(category)
                        if valid_roles_for_category:
                            match_conditions.append(
                                {
                                    "$and": [
                                        {"profile_categories": category},
                                        {
                                            "role_titles": {
                                                "$in": valid_roles_for_category
                                            }
                                        },
                                    ]
                                }
                            )

                elif role_titles and not profile_categories:
                    # Case 3: Only roles specified, no categories
                    # Match any job with these role titles
                    match_conditions.append({"role_titles": {"$in": role_titles}})

                # Build the base query
                base_match = {
                    "source_status": "enriched",
                }

                # Add location filter if specified
                if locations:
                    base_match["country"] = {"$in": locations}

                # Add the OR conditions for category+role matching
                if match_conditions:
                    base_match["$or"] = match_conditions

                # Find matching job listings
                matching_jobs = list(job_listings_collection.find(base_match))
                jobs_found = len(matching_jobs)
                total_jobs_found += jobs_found

                if jobs_found > 0:
                    logger.info(
                        "Found matching jobs for candidate",
                        extra={
                            "candidate_id": str(candidate_id),
                            "jobs_found": jobs_found,
                            "query": base_match,
                        },
                    )

                    # Get existing recommendations for this candidate
                    existing_recs = set()
                    try:
                        existing = recommendation_repo.collection.find(
                            {"candidate_id": ObjectId(str(candidate_id))},
                            {"job_listing_id": 1},
                        )
                        existing_recs = {str(rec["job_listing_id"]) for rec in existing}
                    except Exception as e:
                        logger.warning(f"Error fetching existing recommendations: {e}")

                    # Create recommendations for jobs that don't already have one
                    recommendations_to_create = []

                    for job in matching_jobs:
                        job_id = str(job["_id"])

                        # Skip if recommendation already exists
                        if job_id in existing_recs:
                            continue

                        # Build reason for recommendation
                        matched_categories = []
                        matched_roles = []

                        job_categories = job.get("profile_categories", []) or []
                        job_roles = job.get("role_titles", []) or []

                        for cat in profile_categories:
                            if cat in job_categories:
                                matched_categories.append(cat)

                        for role in role_titles:
                            if role in job_roles:
                                matched_roles.append(role)

                        # Build reason string
                        reason_parts = []
                        if matched_categories:
                            reason_parts.append(
                                f"Categories: {', '.join(matched_categories[:3])}"
                            )
                        if matched_roles:
                            reason_parts.append(
                                f"Roles: {', '.join(matched_roles[:3])}"
                            )

                        reason = "Matches your preferences - " + " | ".join(
                            reason_parts
                        )

                        # Create recommendation object
                        recommendation = RecommendationCreate(
                            candidate_id=str(candidate_id),
                            job_listing_id=job_id,
                            company_id=(
                                str(job.get("company_id"))
                                if job.get("company_id")
                                else None
                            ),
                            reason=reason,
                            recommendation_status="recommended",
                            recommended_at=datetime.now(),
                        )

                        recommendations_to_create.append(recommendation)

                    # Bulk create recommendations if any
                    if recommendations_to_create:
                        try:
                            recommendation_repo.create_recommendations_bulk(
                                recommendations_to_create
                            )

                            logger.info(
                                "Created recommendations for candidate",
                                extra={
                                    "candidate_id": str(candidate_id),
                                    "recommendations": len(recommendations_to_create),
                                },
                            )
                        except Exception as e:
                            error_msg = f"Error creating recommendations for candidate {candidate_id}: {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)

            except Exception as e:
                error_msg = f"Error processing candidate {candidate.get('_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        # Final summary
        result = {
            "status": "completed",
            "total_candidates_processed": total_candidates,
            "total_jobs_found": total_jobs_found,
            "errors": errors,
            "completed_at": datetime.now().isoformat(),
        }

        return result

    except Exception as e:
        error_msg = f"Fatal error in create_recommendations task: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "total_candidates_processed": total_candidates,
        }
