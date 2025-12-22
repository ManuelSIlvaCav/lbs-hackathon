"""
API routes for CV Builder operations.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
import io

from .models import (
    CVBuilderDocument,
    CVBuilderCreate,
    CVBuilderUpdate,
    CVTemplate,
    CVScore,
    EnhanceBulletsRequest,
    EnhanceSummaryRequest,
    EnhancementSuggestion,
    ExportCVRequest,
)
from .repository import CVBuilderRepository
from domains.auth.routes import get_current_active_user
from domains.auth.models import UserInDB
from domains.candidates.repository import candidate_repository
from integrations.agents.cv_enhancement_agent import (
    run_bullet_enhancement,
    run_summary_enhancement,
    run_cv_scoring,
)


router = APIRouter(prefix="/api/cv-builder", tags=["cv-builder"])

# Initialize repository
cv_builder_repository = CVBuilderRepository()
logger = logging.getLogger("app")


def get_candidate_id_from_user(current_user: UserInDB) -> str:
    """Helper to get candidate_id from authenticated user."""
    if not current_user.candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have a candidate profile",
        )
    return current_user.candidate_id


# =========================================================================
# CV Document Endpoints
# =========================================================================


@router.post("/", response_model=CVBuilderDocument, status_code=status.HTTP_201_CREATED)
async def create_cv(
    create_data: CVBuilderCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Create a new CV document.

    If from_parsed_cv is True, will pre-populate from the candidate's parsed CV.
    """
    candidate_id = get_candidate_id_from_user(current_user)

    # Get parsed CV data if requested
    parsed_cv_data = None
    if create_data.from_parsed_cv:
        candidate = candidate_repository.get_candidate_by_id(candidate_id)
        if (
            candidate
            and candidate.metadata
            and candidate.metadata.categorization_schema
        ):
            parsed_cv_data = candidate.metadata.categorization_schema.model_dump()

    try:
        return cv_builder_repository.create_cv(
            candidate_id=candidate_id,
            create_data=create_data,
            parsed_cv_data=parsed_cv_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create CV: {str(e)}",
        )


@router.get("/", response_model=List[CVBuilderDocument])
async def get_my_cvs(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Get all CV documents for the authenticated user."""
    candidate_id = get_candidate_id_from_user(current_user)
    return cv_builder_repository.get_cvs_by_candidate(candidate_id)


@router.get("/primary", response_model=Optional[CVBuilderDocument])
async def get_primary_cv(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Get the primary CV for the authenticated user."""
    candidate_id = get_candidate_id_from_user(current_user)
    cv = cv_builder_repository.get_primary_cv(candidate_id)
    return cv


@router.get("/{cv_id}", response_model=CVBuilderDocument)
async def get_cv(
    cv_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Get a specific CV document by ID."""
    candidate_id = get_candidate_id_from_user(current_user)

    cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )

    # Verify ownership
    if cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own CVs",
        )

    return cv


@router.patch("/{cv_id}", response_model=CVBuilderDocument)
async def update_cv(
    cv_id: str,
    update_data: CVBuilderUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Update a CV document."""
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own CVs",
        )

    updated_cv = cv_builder_repository.update_cv(cv_id, update_data)
    if not updated_cv:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update CV",
        )

    return updated_cv


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv(
    cv_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Delete a CV document."""
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own CVs",
        )

    if not cv_builder_repository.delete_cv(cv_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete CV",
        )


@router.post("/{cv_id}/set-primary", response_model=dict)
async def set_primary_cv(
    cv_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Set a CV as the primary CV."""
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own CVs",
        )

    if cv_builder_repository.set_primary_cv(candidate_id, cv_id):
        return {"success": True, "message": "CV set as primary"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set primary CV",
        )


# =========================================================================
# Template Endpoints
# =========================================================================


@router.get("/templates/all", response_model=List[CVTemplate])
async def get_templates():
    """Get all available CV templates."""
    return cv_builder_repository.get_all_templates()


@router.get("/templates/{template_id}", response_model=CVTemplate)
async def get_template(template_id: str):
    """Get a specific template by ID."""
    template = cv_builder_repository.get_template_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return template


# =========================================================================
# Enhancement Endpoints
# =========================================================================


@router.post("/{cv_id}/enhance-bullets", response_model=EnhancementSuggestion)
async def enhance_bullets(
    cv_id: str,
    request: EnhanceBulletsRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Get AI-powered enhancement suggestions for bullet points.

    Returns enhanced versions of the provided bullets that the user can accept or reject.
    """
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only enhance your own CVs",
        )

    # Get context from the CV
    context = request.context
    role_title = None
    company_name = None

    if request.section_type == "experience":
        for exp in existing_cv.experience:
            if exp.id == request.section_id:
                role_title = exp.role_title
                company_name = exp.company_name
                break

    # Run enhancement agent
    result = await run_bullet_enhancement(
        bullets=request.bullets,
        context=context,
        role_title=role_title,
        company_name=company_name,
        target_job_title=request.target_job_title,
        target_job_description=request.target_job_description,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate enhancements",
        )

    return EnhancementSuggestion(
        section_type=request.section_type,
        section_id=request.section_id,
        enhancement_type="bullet_improvement",
        bullet_enhancements=[
            {
                "original": e.original,
                "enhanced": e.enhanced,
                "explanation": e.explanation,
                "improvements": e.improvements,
            }
            for e in result.enhancements
        ],
        suggested_skills=result.suggested_skills,
        suggested_keywords=result.suggested_keywords,
        target_job_title=request.target_job_title,
        target_job_description=request.target_job_description,
    )


@router.post("/{cv_id}/enhance-summary", response_model=EnhancementSuggestion)
async def enhance_summary(
    cv_id: str,
    request: EnhanceSummaryRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Get AI-powered enhancement for the professional summary.
    """
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only enhance your own CVs",
        )

    # Get experience context from CV
    experience_context = [
        {"role_title": exp.role_title, "company_name": exp.company_name}
        for exp in existing_cv.experience[:3]
    ]

    # Get skills
    skills = existing_cv.skills.technical_skills[:5] + existing_cv.skills.tools[:5]

    # Run enhancement agent
    result = await run_summary_enhancement(
        current_summary=request.current_summary,
        experience_context=experience_context,
        skills=skills,
        target_job_title=request.target_job_title,
        target_job_description=request.target_job_description,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary enhancement",
        )

    return EnhancementSuggestion(
        section_type="summary",
        section_id=None,
        enhancement_type="summary_improvement",
        summary_enhancement=result.enhanced_summary,
        bullet_enhancements=[],
        suggested_skills=[],
        suggested_keywords=[],
        target_job_title=request.target_job_title,
        target_job_description=request.target_job_description,
    )


# =========================================================================
# Scoring Endpoints
# =========================================================================


@router.post("/{cv_id}/score", response_model=CVScore)
async def score_cv(
    cv_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Score a CV for ATS compatibility and quality.

    Returns detailed breakdown of scores and improvement recommendations.
    """
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only score your own CVs",
        )

    # Get template info
    template = cv_builder_repository.get_template_by_id(existing_cv.selected_template)
    template_info = template.model_dump() if template else None

    # Prepare CV data for scoring
    cv_data = existing_cv.model_dump()

    # Run scoring agent
    result = await run_cv_scoring(cv_data, template_info)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to score CV",
        )

    # Save score
    score_data = {
        "overall_score": result.overall_score,
        "breakdown": result.breakdown.model_dump(),
        "top_recommendations": result.top_recommendations,
        "template_used": existing_cv.selected_template,
    }

    score = cv_builder_repository.save_score(cv_id, candidate_id, score_data)

    return score


@router.get("/{cv_id}/score/history", response_model=List[CVScore])
async def get_score_history(
    cv_id: str,
    limit: int = 10,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Get score history for a CV."""
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own CV scores",
        )

    return cv_builder_repository.get_score_history(cv_id, limit)


# =========================================================================
# Export Endpoints
# =========================================================================


@router.post("/{cv_id}/export")
async def export_cv(
    cv_id: str,
    request: ExportCVRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Export CV to PDF format using the selected template.
    """
    candidate_id = get_candidate_id_from_user(current_user)

    # Verify ownership
    existing_cv = cv_builder_repository.get_cv_by_id(cv_id)
    if not existing_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )
    if existing_cv.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only export your own CVs",
        )

    # Get template
    template = cv_builder_repository.get_template_by_id(request.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Generate PDF
    try:
        from .pdf_generator import generate_cv_pdf

        pdf_buffer = generate_cv_pdf(existing_cv, template)

        # Generate filename
        name = existing_cv.contact_info.full_name or "CV"
        filename = f"{name.replace(' ', '_')}_CV.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF generation not yet implemented",
        )
    except Exception as e:
        logger.error(
            "Failed to generate PDF",
            extra={
                "error_msg": str(e),
                "context": "export_cv",
                "candidate_id": candidate_id,
                "cv_id": cv_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}",
        )
