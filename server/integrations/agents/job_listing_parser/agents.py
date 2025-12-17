"""
Agent definitions for job listing parsing.

This module creates the specialized parser agents:
- LinkedIn job parser
- Other job boards parser

Routing is done in the runner based on URL domain checking.
"""

from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

from .schemas import AgentJobCategorizationSchema
from .instructions import (
    get_linkedin_instructions,
    get_other_job_boards_instructions,
)


# Create singleton instances of the specialized parser agents
linkedin_parser_agent = Agent(
    name="LinkedinJobListingParser",
    instructions=get_linkedin_instructions(),
    model="gpt-5-nano",
    output_type=AgentJobCategorizationSchema,
    model_settings=ModelSettings(
        store=True,
        reasoning=Reasoning(effort="low"),
    ),
)

other_job_parser_agent = Agent(
    name="OtherJobListingParser",
    instructions=get_other_job_boards_instructions(),
    model="gpt-5-nano",
    output_type=AgentJobCategorizationSchema,
    model_settings=ModelSettings(
        store=True,
        reasoning=Reasoning(effort="low"),
    ),
)
