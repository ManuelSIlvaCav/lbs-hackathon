"""
CV Builder Domain

Provides CV building, enhancement, scoring, and export functionality.
"""

from .models import (
    CVBuilderDocument,
    CVContactInfo,
    CVEducationItem,
    CVExperienceItem,
    CVSkillsSummary,
    CVTemplate,
    CVScore,
    CVScoreBreakdown,
    EnhancementSuggestion,
    BulletEnhancement,
)
from .repository import CVBuilderRepository
from .routes import router

__all__ = [
    "CVBuilderDocument",
    "CVContactInfo",
    "CVEducationItem",
    "CVExperienceItem",
    "CVSkillsSummary",
    "CVTemplate",
    "CVScore",
    "CVScoreBreakdown",
    "EnhancementSuggestion",
    "BulletEnhancement",
    "CVBuilderRepository",
    "router",
]
