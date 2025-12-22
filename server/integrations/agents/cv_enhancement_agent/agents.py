"""
Agent definitions for CV enhancement.
"""

from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

from .schemas import (
    BulletEnhancementResult,
    SummaryEnhancementResult,
    CVScoreSchema,
)
from .instructions import (
    get_bullet_enhancement_instructions,
    get_summary_enhancement_instructions,
    get_cv_scoring_instructions,
)


# Bullet Enhancement Agent
bullet_enhancement_agent = Agent(
    name="BulletEnhancementAgent",
    instructions=get_bullet_enhancement_instructions(),
    model="gpt-5-nano",
    output_type=BulletEnhancementResult,
    model_settings=ModelSettings(
        store=True,
        reasoning=Reasoning(effort="medium"),
    ),
)


# Summary Enhancement Agent
summary_enhancement_agent = Agent(
    name="SummaryEnhancementAgent",
    instructions=get_summary_enhancement_instructions(),
    model="gpt-5-nano",
    output_type=SummaryEnhancementResult,
    model_settings=ModelSettings(
        store=True,
        reasoning=Reasoning(effort="medium"),
    ),
)


# CV Scoring Agent
cv_scoring_agent = Agent(
    name="CVScoringAgent",
    instructions=get_cv_scoring_instructions(),
    model="gpt-5-nano",
    output_type=CVScoreSchema,
    model_settings=ModelSettings(
        store=True,
        reasoning=Reasoning(effort="medium"),
    ),
)
