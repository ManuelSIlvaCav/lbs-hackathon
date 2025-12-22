"""
Schema definitions for CV enhancement agent outputs.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Bullet Enhancement Schemas
# ============================================================================


class BulletEnhancementSchema(BaseModel):
    """Schema for a single bullet enhancement"""

    original: str = Field(..., description="Original bullet text")
    enhanced: str = Field(..., description="Enhanced bullet text")
    explanation: str = Field(..., description="Brief explanation of improvements made")
    improvements: List[str] = Field(
        default_factory=list,
        description="List of specific improvements (e.g., 'Added metrics', 'Used stronger action verb')",
    )


class BulletEnhancementResult(BaseModel):
    """Result from bullet enhancement agent"""

    enhancements: List[BulletEnhancementSchema] = Field(
        default_factory=list, description="List of enhanced bullets"
    )
    suggested_skills: List[str] = Field(
        default_factory=list,
        description="Skills detected from bullets to add to skills section",
    )
    suggested_keywords: List[str] = Field(
        default_factory=list,
        description="ATS keywords to consider incorporating",
    )


# ============================================================================
# Summary Enhancement Schemas
# ============================================================================


class SummaryEnhancementResult(BaseModel):
    """Result from summary enhancement agent"""

    enhanced_summary: str = Field(..., description="Enhanced summary text")
    explanation: str = Field(..., description="What was improved and why")
    key_improvements: List[str] = Field(
        default_factory=list, description="List of key improvements made"
    )
    alternative_versions: List[str] = Field(
        default_factory=list,
        description="Alternative summary versions for different focuses",
    )


# ============================================================================
# Scoring Schemas
# ============================================================================


class ScoreCategoryEnum(str, Enum):
    """Categories for CV scoring"""

    KEYWORD_OPTIMIZATION = "keyword_optimization"
    FORMAT_COMPLIANCE = "format_compliance"
    CONTENT_QUALITY = "content_quality"
    SECTION_COMPLETENESS = "section_completeness"
    ACTION_VERBS = "action_verbs"
    QUANTIFICATION = "quantification"
    LENGTH_OPTIMIZATION = "length_optimization"


class CVScoreItemSchema(BaseModel):
    """Individual score item"""

    category: ScoreCategoryEnum = Field(..., description="Score category")
    score: int = Field(..., ge=0, le=100, description="Score out of 100")
    weight: float = Field(default=1.0, description="Weight for overall score")
    feedback: str = Field(..., description="Feedback message")
    suggestions: List[str] = Field(
        default_factory=list, description="Specific improvement suggestions"
    )


class CVScoreBreakdownSchema(BaseModel):
    """Detailed score breakdown"""

    keyword_optimization: CVScoreItemSchema = Field(
        ..., description="Keyword usage and density score"
    )
    format_compliance: CVScoreItemSchema = Field(
        ..., description="ATS format compliance score"
    )
    content_quality: CVScoreItemSchema = Field(
        ..., description="Content quality and clarity score"
    )
    section_completeness: CVScoreItemSchema = Field(
        ..., description="Completeness of sections score"
    )
    action_verbs: CVScoreItemSchema = Field(
        ..., description="Use of strong action verbs score"
    )
    quantification: CVScoreItemSchema = Field(
        ..., description="Use of metrics and quantification score"
    )
    length_optimization: CVScoreItemSchema = Field(
        ..., description="CV length optimization score"
    )


class CVScoreSchema(BaseModel):
    """Complete CV scoring result"""

    overall_score: int = Field(..., ge=0, le=100, description="Overall ATS score")
    breakdown: CVScoreBreakdownSchema = Field(
        ..., description="Detailed score breakdown"
    )
    top_recommendations: List[str] = Field(
        default_factory=list,
        description="Top 3-5 prioritized improvement recommendations",
    )
    strengths: List[str] = Field(
        default_factory=list, description="Key strengths of the CV"
    )
    critical_issues: List[str] = Field(
        default_factory=list,
        description="Critical issues that may cause ATS rejection",
    )
