"""
Repository for CV Builder CRUD operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING

from database import get_collection
from .models import (
    CVBuilderDocument,
    CVBuilderCreate,
    CVBuilderUpdate,
    CVTemplate,
    CVScore,
    CVContactInfo,
    CVExperienceItem,
    CVEducationItem,
    CVSkillsSummary,
    CVSummary,
)


class CVBuilderRepository:
    """Repository for CV Builder document operations"""

    def __init__(self):
        self.collection: Collection = get_collection("cv_builder")
        self.templates_collection: Collection = get_collection("cv_templates")
        self.scores_collection: Collection = get_collection("cv_scores")
        self._ensure_indexes()
        self._seed_default_templates()

    def _ensure_indexes(self):
        """Create indexes for better query performance"""
        try:
            # CV Builder indexes
            self.collection.create_index(
                [("candidate_id", ASCENDING)],
                name="candidate_id_index",
                background=True,
            )
            self.collection.create_index(
                [("candidate_id", ASCENDING), ("is_primary", DESCENDING)],
                name="candidate_primary_cv_index",
                background=True,
            )

            # Templates indexes
            self.templates_collection.create_index(
                [("template_id", ASCENDING)],
                name="template_id_index",
                unique=True,
                background=True,
            )

            # Scores indexes
            self.scores_collection.create_index(
                [("cv_id", ASCENDING), ("scored_at", DESCENDING)],
                name="cv_scores_index",
                background=True,
            )

            print("✓ CV Builder indexes created successfully")
        except Exception as e:
            print(f"Note: Index creation handled by MongoDB: {e}")

    def _seed_default_templates(self):
        """Seed default ATS-friendly templates if not exist"""
        default_templates = [
            {
                "template_id": "classic",
                "name": "Classic Professional",
                "description": "Clean, traditional layout perfect for corporate roles. Single-column design ensures 100% ATS compatibility.",
                "font_family": "Arial",
                "font_size_base": 11,
                "accent_color": "#2563eb",
                "line_spacing": 1.15,
                "margins": {"top": 0.5, "bottom": 0.5, "left": 0.5, "right": 0.5},
                "sections": [
                    {"name": "contact", "order": 1, "visible": True},
                    {"name": "summary", "order": 2, "visible": True},
                    {"name": "experience", "order": 3, "visible": True},
                    {"name": "education", "order": 4, "visible": True},
                    {"name": "skills", "order": 5, "visible": True},
                    {"name": "projects", "order": 6, "visible": False},
                ],
                "is_ats_friendly": True,
                "uses_columns": False,
                "uses_graphics": False,
                "is_default": True,
            },
            {
                "template_id": "modern",
                "name": "Modern Minimal",
                "description": "Contemporary design with subtle styling. Clean lines and strategic whitespace for easy readability.",
                "font_family": "Calibri",
                "font_size_base": 11,
                "accent_color": "#0f172a",
                "line_spacing": 1.2,
                "margins": {"top": 0.6, "bottom": 0.6, "left": 0.6, "right": 0.6},
                "sections": [
                    {"name": "contact", "order": 1, "visible": True},
                    {"name": "summary", "order": 2, "visible": True},
                    {"name": "experience", "order": 3, "visible": True},
                    {"name": "skills", "order": 4, "visible": True},
                    {"name": "education", "order": 5, "visible": True},
                    {"name": "projects", "order": 6, "visible": False},
                ],
                "is_ats_friendly": True,
                "uses_columns": False,
                "uses_graphics": False,
                "is_default": False,
            },
            {
                "template_id": "executive",
                "name": "Executive",
                "description": "Sophisticated design for senior professionals. Emphasizes leadership and strategic achievements.",
                "font_family": "Georgia",
                "font_size_base": 11,
                "accent_color": "#1e3a5f",
                "line_spacing": 1.15,
                "margins": {"top": 0.5, "bottom": 0.5, "left": 0.6, "right": 0.6},
                "sections": [
                    {"name": "contact", "order": 1, "visible": True},
                    {"name": "summary", "order": 2, "visible": True},
                    {"name": "experience", "order": 3, "visible": True},
                    {"name": "education", "order": 4, "visible": True},
                    {"name": "skills", "order": 5, "visible": True},
                    {"name": "projects", "order": 6, "visible": False},
                ],
                "is_ats_friendly": True,
                "uses_columns": False,
                "uses_graphics": False,
                "is_default": False,
            },
            {
                "template_id": "tech",
                "name": "Tech Professional",
                "description": "Optimized for technical roles. Highlights skills and projects prominently.",
                "font_family": "Roboto",
                "font_size_base": 10,
                "accent_color": "#059669",
                "line_spacing": 1.1,
                "margins": {"top": 0.4, "bottom": 0.4, "left": 0.5, "right": 0.5},
                "sections": [
                    {"name": "contact", "order": 1, "visible": True},
                    {"name": "summary", "order": 2, "visible": True},
                    {"name": "skills", "order": 3, "visible": True},
                    {"name": "experience", "order": 4, "visible": True},
                    {"name": "projects", "order": 5, "visible": True},
                    {"name": "education", "order": 6, "visible": True},
                ],
                "is_ats_friendly": True,
                "uses_columns": False,
                "uses_graphics": False,
                "is_default": False,
            },
        ]

        for template_data in default_templates:
            # Use upsert to avoid duplicates
            self.templates_collection.update_one(
                {"template_id": template_data["template_id"]},
                {
                    "$set": template_data,
                    "$setOnInsert": {"created_at": datetime.now()},
                },
                upsert=True,
            )

    # =========================================================================
    # CV Document Operations
    # =========================================================================

    def create_cv(
        self,
        candidate_id: str,
        create_data: CVBuilderCreate,
        parsed_cv_data: Optional[Dict[str, Any]] = None,
    ) -> CVBuilderDocument:
        """
        Create a new CV document.

        Args:
            candidate_id: ID of the candidate
            create_data: Creation parameters
            parsed_cv_data: Optional parsed CV data to pre-populate

        Returns:
            Created CVBuilderDocument
        """
        # Initialize with defaults
        cv_doc = {
            "candidate_id": candidate_id,
            "name": create_data.name,
            "selected_template": create_data.selected_template,
            "contact_info": {"full_name": ""},
            "summary": {"text": ""},
            "experience": [],
            "education": [],
            "skills": {
                "technical_skills": [],
                "soft_skills": [],
                "tools": [],
                "languages": [],
                "certifications": [],
            },
            "projects": [],
            "is_primary": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "latest_score": None,
        }

        # Pre-populate from parsed CV if requested
        if create_data.from_parsed_cv and parsed_cv_data:
            cv_doc = self._populate_from_parsed_cv(cv_doc, parsed_cv_data)

        # Check if this should be primary (first CV for candidate)
        existing_count = self.collection.count_documents({"candidate_id": candidate_id})
        if existing_count == 0:
            cv_doc["is_primary"] = True

        result = self.collection.insert_one(cv_doc)
        cv_doc["_id"] = str(result.inserted_id)

        return CVBuilderDocument(**cv_doc)

    def _populate_from_parsed_cv(
        self, cv_doc: Dict[str, Any], parsed_cv: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Populate CV document from parsed CV data."""
        # Contact info
        contact = parsed_cv.get("contact_info", {})
        cv_doc["contact_info"] = {
            "full_name": contact.get("full_name", ""),
            "email": contact.get("email"),
            "phone": contact.get("phone"),
            "linkedin": contact.get("linkedin"),
            "location": None,  # Not in parsed CV
            "website": None,
            "other_links": contact.get("other_links", []),
        }

        # Experience
        experience = parsed_cv.get("experience", [])
        cv_doc["experience"] = [
            {
                "id": str(ObjectId()),
                "company_name": exp.get("company_name", ""),
                "role_title": exp.get("role_title", ""),
                "location": exp.get("location"),
                "start_date": exp.get("start_date"),
                "end_date": exp.get("end_date"),
                "is_current": exp.get("end_date") is None,
                "description": exp.get("summary"),
                "bullets": exp.get("bullets", []),  # Now includes parsed bullets
            }
            for exp in experience
        ]

        # Education
        education = parsed_cv.get("education", [])
        cv_doc["education"] = [
            {
                "id": str(ObjectId()),
                "institution": edu.get("institution", ""),
                "degree_type": edu.get("degree_type"),
                "degree_name": edu.get("degree_name"),
                "major": edu.get("major"),
                "start_date": edu.get("start_date"),
                "end_date": edu.get("end_date"),
                "grades": edu.get("grades"),
                "description": edu.get("description"),
                "bullets": [],
            }
            for edu in education
        ]

        # Skills
        skills = parsed_cv.get("skills_summary", {})
        cv_doc["skills"] = {
            "technical_skills": skills.get("hard_skills_overall", []),
            "soft_skills": skills.get("soft_skills_overall", []),
            "tools": skills.get("software_knowledge", []),
            "languages": skills.get("languages", []),
            "certifications": [],
        }

        return cv_doc

    def get_cv_by_id(self, cv_id: str) -> Optional[CVBuilderDocument]:
        """Get a CV document by ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(cv_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return CVBuilderDocument(**doc)
            return None
        except Exception:
            return None

    def get_cvs_by_candidate(self, candidate_id: str) -> List[CVBuilderDocument]:
        """Get all CV documents for a candidate."""
        docs = self.collection.find({"candidate_id": candidate_id}).sort(
            [("is_primary", DESCENDING), ("updated_at", DESCENDING)]
        )
        result = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            result.append(CVBuilderDocument(**doc))
        return result

    def get_primary_cv(self, candidate_id: str) -> Optional[CVBuilderDocument]:
        """Get the primary CV for a candidate."""
        doc = self.collection.find_one(
            {"candidate_id": candidate_id, "is_primary": True}
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            return CVBuilderDocument(**doc)
        return None

    def update_cv(
        self, cv_id: str, update_data: CVBuilderUpdate
    ) -> Optional[CVBuilderDocument]:
        """Update a CV document."""
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now()

        # Handle nested models
        if "contact_info" in update_dict and update_dict["contact_info"]:
            update_dict["contact_info"] = update_dict["contact_info"]
        if "summary" in update_dict and update_dict["summary"]:
            update_dict["summary"] = update_dict["summary"]
        if "skills" in update_dict and update_dict["skills"]:
            update_dict["skills"] = update_dict["skills"]

        # Convert experience/education items
        if "experience" in update_dict and update_dict["experience"]:
            update_dict["experience"] = [
                exp.model_dump() if hasattr(exp, "model_dump") else exp
                for exp in update_dict["experience"]
            ]
        if "education" in update_dict and update_dict["education"]:
            update_dict["education"] = [
                edu.model_dump() if hasattr(edu, "model_dump") else edu
                for edu in update_dict["education"]
            ]
        if "projects" in update_dict and update_dict["projects"]:
            update_dict["projects"] = [
                proj.model_dump() if hasattr(proj, "model_dump") else proj
                for proj in update_dict["projects"]
            ]

        try:
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(cv_id)},
                {"$set": update_dict},
                return_document=True,
            )
            if result:
                result["_id"] = str(result["_id"])
                return CVBuilderDocument(**result)
            return None
        except Exception as e:
            print(f"Error updating CV: {e}")
            return None

    def delete_cv(self, cv_id: str) -> bool:
        """Delete a CV document."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(cv_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    def set_primary_cv(self, candidate_id: str, cv_id: str) -> bool:
        """Set a CV as the primary CV for a candidate."""
        try:
            # Unset current primary
            self.collection.update_many(
                {"candidate_id": candidate_id, "is_primary": True},
                {"$set": {"is_primary": False}},
            )
            # Set new primary
            result = self.collection.update_one(
                {"_id": ObjectId(cv_id), "candidate_id": candidate_id},
                {"$set": {"is_primary": True}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    # =========================================================================
    # Template Operations
    # =========================================================================

    def get_all_templates(self) -> List[CVTemplate]:
        """Get all available templates."""
        docs = self.templates_collection.find().sort("name", ASCENDING)
        result = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            result.append(CVTemplate(**doc))
        return result

    def get_template_by_id(self, template_id: str) -> Optional[CVTemplate]:
        """Get a template by its ID."""
        doc = self.templates_collection.find_one({"template_id": template_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return CVTemplate(**doc)
        return None

    # =========================================================================
    # Score Operations
    # =========================================================================

    def save_score(
        self, cv_id: str, candidate_id: str, score_data: Dict[str, Any]
    ) -> CVScore:
        """Save a CV score."""
        score_doc = {
            "cv_id": cv_id,
            "candidate_id": candidate_id,
            "overall_score": score_data.get("overall_score", 0),
            "breakdown": score_data.get("breakdown", {}),
            "top_recommendations": score_data.get("top_recommendations", []),
            "scored_at": datetime.now(),
            "template_used": score_data.get("template_used"),
        }

        result = self.scores_collection.insert_one(score_doc)
        score_doc["_id"] = str(result.inserted_id)

        # Update cached score on CV document
        self.collection.update_one(
            {"_id": ObjectId(cv_id)},
            {
                "$set": {
                    "latest_score": score_doc,
                    "updated_at": datetime.now(),
                }
            },
        )

        return CVScore(**score_doc)

    def get_latest_score(self, cv_id: str) -> Optional[CVScore]:
        """Get the latest score for a CV."""
        doc = self.scores_collection.find_one(
            {"cv_id": cv_id}, sort=[("scored_at", DESCENDING)]
        )
        if doc:
            doc["_id"] = str(doc["_id"])
            return CVScore(**doc)
        return None

    def get_score_history(self, cv_id: str, limit: int = 10) -> List[CVScore]:
        """Get score history for a CV."""
        docs = (
            self.scores_collection.find({"cv_id": cv_id})
            .sort("scored_at", DESCENDING)
            .limit(limit)
        )
        result = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            result.append(CVScore(**doc))
        return result
