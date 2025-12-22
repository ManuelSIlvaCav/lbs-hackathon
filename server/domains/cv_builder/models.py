"""
Models for CV Builder domain.

Includes CV document structure, templates, scoring, and enhancement suggestions.
"""

from typing import Annotated, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from bson import ObjectId

# Custom type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


# ============================================================================
# CV Content Models
# ============================================================================


class CVContactInfo(BaseModel):
    """Contact information section of CV"""

    full_name: str = Field(..., description="Full name of the candidate")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    location: Optional[str] = Field(
        default=None, description="Current location (city, country)"
    )
    website: Optional[str] = Field(
        default=None, description="Personal website or portfolio URL"
    )
    other_links: List[str] = Field(
        default_factory=list, description="Other relevant links (GitHub, etc.)"
    )


class CVEducationItem(BaseModel):
    """Education entry in CV"""

    id: str = Field(
        default_factory=lambda: str(ObjectId()), description="Unique identifier"
    )
    institution: str = Field(..., description="Name of institution")
    degree_type: Optional[str] = Field(
        default=None, description="Type of degree (Bachelor, Master, PhD, etc.)"
    )
    degree_name: Optional[str] = Field(
        default=None, description="Name of the degree/program"
    )
    major: Optional[str] = Field(default=None, description="Major or field of study")
    start_date: Optional[str] = Field(default=None, description="Start date")
    end_date: Optional[str] = Field(
        default=None, description="End date (null if current)"
    )
    grades: Optional[str] = Field(
        default=None, description="GPA, classification, or grades"
    )
    description: Optional[str] = Field(
        default=None,
        description="Additional details, achievements, or relevant coursework",
    )
    bullets: List[str] = Field(
        default_factory=list, description="Bullet points for achievements"
    )


class CVExperienceItem(BaseModel):
    """Work experience entry in CV"""

    id: str = Field(
        default_factory=lambda: str(ObjectId()), description="Unique identifier"
    )
    company_name: str = Field(..., description="Company name")
    role_title: str = Field(..., description="Job title")
    location: Optional[str] = Field(default=None, description="Location of the role")
    start_date: Optional[str] = Field(default=None, description="Start date")
    end_date: Optional[str] = Field(
        default=None, description="End date (null if current)"
    )
    is_current: bool = Field(default=False, description="Whether this is current role")
    description: Optional[str] = Field(
        default=None, description="Brief description of the role"
    )
    bullets: List[str] = Field(
        default_factory=list,
        description="Achievement/responsibility bullet points",
    )


class CVSkillsSummary(BaseModel):
    """Skills section of CV"""

    technical_skills: List[str] = Field(
        default_factory=list, description="Technical/hard skills"
    )
    soft_skills: List[str] = Field(
        default_factory=list, description="Soft/interpersonal skills"
    )
    tools: List[str] = Field(
        default_factory=list, description="Tools and software proficiency"
    )
    languages: List[str] = Field(
        default_factory=list, description="Languages with proficiency levels"
    )
    certifications: List[str] = Field(
        default_factory=list, description="Professional certifications"
    )


class CVProject(BaseModel):
    """Project entry in CV (optional section)"""

    id: str = Field(
        default_factory=lambda: str(ObjectId()), description="Unique identifier"
    )
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    url: Optional[str] = Field(default=None, description="Project URL or link")
    technologies: List[str] = Field(
        default_factory=list, description="Technologies used"
    )
    bullets: List[str] = Field(
        default_factory=list, description="Key achievements or contributions"
    )


class CVSummary(BaseModel):
    """Professional summary section"""

    text: str = Field(default="", description="Professional summary text")


# ============================================================================
# CV Document Model
# ============================================================================


class CVBuilderDocument(BaseModel):
    """Main CV document stored in database"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    candidate_id: str = Field(..., description="Reference to candidate")

    # CV Sections
    contact_info: CVContactInfo = Field(..., description="Contact information")
    summary: CVSummary = Field(
        default_factory=CVSummary, description="Professional summary"
    )
    experience: List[CVExperienceItem] = Field(
        default_factory=list, description="Work experience entries"
    )
    education: List[CVEducationItem] = Field(
        default_factory=list, description="Education entries"
    )
    skills: CVSkillsSummary = Field(
        default_factory=CVSkillsSummary, description="Skills summary"
    )
    projects: List[CVProject] = Field(
        default_factory=list, description="Optional projects section"
    )

    # Template and styling
    selected_template: str = Field(
        default="classic", description="Selected template ID"
    )

    # Metadata
    name: str = Field(default="My CV", description="Name of this CV version")
    is_primary: bool = Field(
        default=False, description="Whether this is the primary CV"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Latest score (cached)
    latest_score: Optional["CVScore"] = Field(
        default=None, description="Cached latest ATS score"
    )


# ============================================================================
# Template Models
# ============================================================================


class TemplateSection(BaseModel):
    """Configuration for a section in a template"""

    name: str = Field(..., description="Section name")
    order: int = Field(..., description="Order in the template")
    visible: bool = Field(default=True, description="Whether section is visible")


class CVTemplate(BaseModel):
    """CV Template definition"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., description="Template display name")
    template_id: str = Field(..., description="Unique template identifier")
    description: str = Field(default="", description="Template description")
    preview_image: Optional[str] = Field(
        default=None, description="URL to preview image"
    )

    # Template styling
    font_family: str = Field(default="Arial", description="Primary font")
    font_size_base: int = Field(default=11, description="Base font size in pt")
    accent_color: str = Field(default="#2563eb", description="Accent color hex")
    line_spacing: float = Field(default=1.15, description="Line spacing multiplier")
    margins: Dict[str, float] = Field(
        default_factory=lambda: {"top": 0.5, "bottom": 0.5, "left": 0.5, "right": 0.5},
        description="Page margins in inches",
    )

    # Section configuration
    sections: List[TemplateSection] = Field(
        default_factory=list, description="Section order and visibility"
    )

    # ATS optimization flags
    is_ats_friendly: bool = Field(default=True, description="ATS-friendly template")
    uses_columns: bool = Field(
        default=False, description="Uses multi-column layout (less ATS-friendly)"
    )
    uses_graphics: bool = Field(
        default=False, description="Uses graphics/icons (less ATS-friendly)"
    )

    # Metadata
    is_default: bool = Field(default=False, description="Default template")
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Scoring Models
# ============================================================================


class ScoreCategory(str, Enum):
    """Categories for CV scoring"""

    KEYWORD_OPTIMIZATION = "keyword_optimization"
    FORMAT_COMPLIANCE = "format_compliance"
    CONTENT_QUALITY = "content_quality"
    SECTION_COMPLETENESS = "section_completeness"
    ACTION_VERBS = "action_verbs"
    QUANTIFICATION = "quantification"
    LENGTH_OPTIMIZATION = "length_optimization"


class CVScoreItem(BaseModel):
    """Individual score item with feedback"""

    category: ScoreCategory = Field(..., description="Score category")
    score: int = Field(..., ge=0, le=100, description="Score out of 100")
    weight: float = Field(default=1.0, description="Weight for overall score")
    feedback: str = Field(..., description="Feedback message")
    suggestions: List[str] = Field(
        default_factory=list, description="Specific improvement suggestions"
    )


class CVScoreBreakdown(BaseModel):
    """Detailed breakdown of CV scores"""

    keyword_optimization: CVScoreItem = Field(
        ..., description="Keyword usage and density"
    )
    format_compliance: CVScoreItem = Field(..., description="ATS format compliance")
    content_quality: CVScoreItem = Field(..., description="Content quality and clarity")
    section_completeness: CVScoreItem = Field(
        ..., description="Completeness of sections"
    )
    action_verbs: CVScoreItem = Field(..., description="Use of strong action verbs")
    quantification: CVScoreItem = Field(
        ..., description="Use of metrics and quantification"
    )
    length_optimization: CVScoreItem = Field(..., description="CV length optimization")


class CVScore(BaseModel):
    """Overall CV score with breakdown"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat() if v else None},
    )

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    cv_id: str = Field(..., description="Reference to CV document")
    candidate_id: str = Field(..., description="Reference to candidate")

    # Scores
    overall_score: int = Field(..., ge=0, le=100, description="Overall ATS score")
    breakdown: CVScoreBreakdown = Field(..., description="Detailed score breakdown")

    # Top recommendations
    top_recommendations: List[str] = Field(
        default_factory=list, description="Top 3-5 improvement recommendations"
    )

    # Metadata
    scored_at: datetime = Field(default_factory=datetime.now)
    template_used: Optional[str] = Field(
        default=None, description="Template ID when scored"
    )


# ============================================================================
# Enhancement Models
# ============================================================================


class EnhancementType(str, Enum):
    """Types of enhancements"""

    BULLET_IMPROVEMENT = "bullet_improvement"
    SUMMARY_IMPROVEMENT = "summary_improvement"
    SKILL_SUGGESTION = "skill_suggestion"
    KEYWORD_ADDITION = "keyword_addition"


class BulletEnhancement(BaseModel):
    """Enhancement suggestion for a single bullet point"""

    original: str = Field(..., description="Original bullet text")
    enhanced: str = Field(..., description="Enhanced bullet text")
    explanation: str = Field(..., description="Why this enhancement helps")
    improvements: List[str] = Field(
        default_factory=list,
        description="List of specific improvements made",
    )


class EnhancementSuggestion(BaseModel):
    """Collection of enhancement suggestions for a CV section"""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
    )

    section_type: str = Field(
        ..., description="Section being enhanced (experience, education, summary)"
    )
    section_id: Optional[str] = Field(
        default=None, description="ID of the specific item (for experience/education)"
    )
    enhancement_type: EnhancementType = Field(..., description="Type of enhancement")

    # The suggestions
    bullet_enhancements: List[BulletEnhancement] = Field(
        default_factory=list, description="Bullet point enhancements"
    )
    summary_enhancement: Optional[str] = Field(
        default=None, description="Enhanced summary text"
    )
    suggested_skills: List[str] = Field(
        default_factory=list, description="Skills to add based on content"
    )
    suggested_keywords: List[str] = Field(
        default_factory=list, description="Keywords to incorporate"
    )

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    target_job_title: Optional[str] = Field(
        default=None, description="Job title used for context"
    )
    target_job_description: Optional[str] = Field(
        default=None, description="Job description used for context"
    )


# ============================================================================
# Request/Response Models
# ============================================================================


class CVBuilderCreate(BaseModel):
    """Request model for creating a new CV"""

    name: str = Field(default="My CV", description="Name for the CV")
    from_parsed_cv: bool = Field(
        default=True, description="Pre-populate from parsed CV"
    )
    selected_template: str = Field(default="classic", description="Initial template")


class CVBuilderUpdate(BaseModel):
    """Request model for updating CV sections"""

    contact_info: Optional[CVContactInfo] = None
    summary: Optional[CVSummary] = None
    experience: Optional[List[CVExperienceItem]] = None
    education: Optional[List[CVEducationItem]] = None
    skills: Optional[CVSkillsSummary] = None
    projects: Optional[List[CVProject]] = None
    selected_template: Optional[str] = None
    name: Optional[str] = None


class EnhanceBulletsRequest(BaseModel):
    """Request to enhance bullets for a section"""

    section_type: str = Field(
        ..., description="Section type: 'experience', 'education', 'project'"
    )
    section_id: str = Field(..., description="ID of the section item")
    bullets: List[str] = Field(..., description="Current bullets to enhance")
    context: Optional[str] = Field(
        default=None,
        description="Additional context (job title, company, etc.)",
    )
    target_job_title: Optional[str] = Field(
        default=None, description="Target job to optimize for"
    )
    target_job_description: Optional[str] = Field(
        default=None, description="Target job description for keyword matching"
    )


class EnhanceSummaryRequest(BaseModel):
    """Request to enhance professional summary"""

    current_summary: str = Field(..., description="Current summary text")
    experience_context: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Experience items for context"
    )
    target_job_title: Optional[str] = Field(
        default=None, description="Target job to optimize for"
    )
    target_job_description: Optional[str] = Field(
        default=None, description="Target job description"
    )


class ExportCVRequest(BaseModel):
    """Request to export CV"""

    template_id: str = Field(..., description="Template to use for export")
    format: str = Field(default="pdf", description="Export format (pdf, docx)")


class ApplyEnhancementRequest(BaseModel):
    """Request to apply an enhancement suggestion"""

    section_type: str = Field(..., description="Section type")
    section_id: Optional[str] = Field(default=None, description="Section item ID")
    enhancement_index: int = Field(..., description="Index of the enhancement to apply")
    enhanced_text: str = Field(..., description="The enhanced text to apply")


# Update forward references
CVBuilderDocument.model_rebuild()
