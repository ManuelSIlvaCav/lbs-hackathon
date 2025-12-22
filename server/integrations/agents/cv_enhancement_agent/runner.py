"""
Runner functions for CV enhancement agents.
"""

from typing import Any, Dict, List, Optional
from agents import Runner

from .agents import (
    bullet_enhancement_agent,
    summary_enhancement_agent,
    cv_scoring_agent,
)
from .schemas import (
    BulletEnhancementResult,
    SummaryEnhancementResult,
    CVScoreSchema,
)


async def run_bullet_enhancement(
    bullets: List[str],
    context: Optional[str] = None,
    role_title: Optional[str] = None,
    company_name: Optional[str] = None,
    target_job_title: Optional[str] = None,
    target_job_description: Optional[str] = None,
) -> Optional[BulletEnhancementResult]:
    """
    Run the bullet enhancement agent.

    Args:
        bullets: List of bullet points to enhance
        context: Additional context about the role
        role_title: Title of the role these bullets are from
        company_name: Company name for context
        target_job_title: Target job to optimize for
        target_job_description: Target job description for keyword matching

    Returns:
        BulletEnhancementResult or None if failed
    """
    try:
        # Build the prompt
        prompt_parts = ["Please enhance the following CV bullet points:\n"]

        if role_title:
            prompt_parts.append(f"Role: {role_title}")
        if company_name:
            prompt_parts.append(f"Company: {company_name}")
        if context:
            prompt_parts.append(f"Context: {context}")

        prompt_parts.append("\nBullet points to enhance:")
        for i, bullet in enumerate(bullets, 1):
            prompt_parts.append(f"{i}. {bullet}")

        if target_job_title:
            prompt_parts.append(f"\nTarget Job Title: {target_job_title}")
            prompt_parts.append("Optimize the bullets to align with this target role.")

        if target_job_description:
            prompt_parts.append(f"\nTarget Job Description:\n{target_job_description}")
            prompt_parts.append(
                "Incorporate relevant keywords from the job description."
            )

        prompt = "\n".join(prompt_parts)

        result = await Runner.run(
            bullet_enhancement_agent,
            [{"role": "user", "content": prompt}],
        )

        return result.final_output

    except Exception as e:
        print(f"Error running bullet enhancement: {e}")
        return None


async def run_summary_enhancement(
    current_summary: str,
    experience_context: Optional[List[Dict[str, Any]]] = None,
    skills: Optional[List[str]] = None,
    target_job_title: Optional[str] = None,
    target_job_description: Optional[str] = None,
) -> Optional[SummaryEnhancementResult]:
    """
    Run the summary enhancement agent.

    Args:
        current_summary: Current professional summary text
        experience_context: List of experience items for context
        skills: List of skills for context
        target_job_title: Target job to optimize for
        target_job_description: Target job description

    Returns:
        SummaryEnhancementResult or None if failed
    """
    try:
        prompt_parts = ["Please enhance the following professional summary:\n"]
        prompt_parts.append(f'Current Summary: "{current_summary}"')

        if experience_context:
            prompt_parts.append("\nExperience Context:")
            for exp in experience_context[:3]:  # Limit to top 3 for context
                role = exp.get("role_title", "Unknown Role")
                company = exp.get("company_name", "Unknown Company")
                prompt_parts.append(f"- {role} at {company}")

        if skills:
            prompt_parts.append(f"\nKey Skills: {', '.join(skills[:10])}")

        if target_job_title:
            prompt_parts.append(f"\nTarget Job Title: {target_job_title}")

        if target_job_description:
            prompt_parts.append(f"\nTarget Job Description:\n{target_job_description}")

        prompt = "\n".join(prompt_parts)

        result = await Runner.run(
            summary_enhancement_agent,
            [{"role": "user", "content": prompt}],
        )

        return result.final_output

    except Exception as e:
        print(f"Error running summary enhancement: {e}")
        return None


async def run_cv_scoring(
    cv_data: Dict[str, Any],
    template_info: Optional[Dict[str, Any]] = None,
) -> Optional[CVScoreSchema]:
    """
    Run the CV scoring agent.

    Args:
        cv_data: Complete CV data dictionary
        template_info: Template information for format scoring

    Returns:
        CVScoreSchema or None if failed
    """
    try:
        prompt_parts = ["Please score the following CV:\n"]

        # Contact info
        contact = cv_data.get("contact_info", {})
        prompt_parts.append("## CONTACT INFORMATION")
        prompt_parts.append(f"Name: {contact.get('full_name', 'Not provided')}")
        prompt_parts.append(f"Email: {contact.get('email', 'Not provided')}")
        prompt_parts.append(f"Phone: {contact.get('phone', 'Not provided')}")
        prompt_parts.append(f"LinkedIn: {contact.get('linkedin', 'Not provided')}")
        prompt_parts.append(f"Location: {contact.get('location', 'Not provided')}")

        # Summary
        summary = cv_data.get("summary", {})
        prompt_parts.append("\n## PROFESSIONAL SUMMARY")
        prompt_parts.append(summary.get("text", "No summary provided"))

        # Experience
        experience = cv_data.get("experience", [])
        prompt_parts.append("\n## WORK EXPERIENCE")
        for exp in experience:
            prompt_parts.append(
                f"\n### {exp.get('role_title', 'Unknown')} at {exp.get('company_name', 'Unknown')}"
            )
            prompt_parts.append(
                f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}"
            )
            bullets = exp.get("bullets", [])
            for bullet in bullets:
                prompt_parts.append(f"• {bullet}")

        # Education
        education = cv_data.get("education", [])
        prompt_parts.append("\n## EDUCATION")
        for edu in education:
            degree = edu.get("degree_type", "")
            name = edu.get("degree_name", "")
            institution = edu.get("institution", "Unknown")
            prompt_parts.append(f"- {degree} {name} at {institution}")

        # Skills
        skills = cv_data.get("skills", {})
        prompt_parts.append("\n## SKILLS")
        tech_skills = skills.get("technical_skills", [])
        if tech_skills:
            prompt_parts.append(f"Technical: {', '.join(tech_skills)}")
        soft_skills = skills.get("soft_skills", [])
        if soft_skills:
            prompt_parts.append(f"Soft Skills: {', '.join(soft_skills)}")
        tools = skills.get("tools", [])
        if tools:
            prompt_parts.append(f"Tools: {', '.join(tools)}")
        languages = skills.get("languages", [])
        if languages:
            prompt_parts.append(f"Languages: {', '.join(languages)}")

        # Template info for format scoring
        if template_info:
            prompt_parts.append("\n## TEMPLATE INFORMATION")
            prompt_parts.append(f"Template: {template_info.get('name', 'Unknown')}")
            prompt_parts.append(
                f"ATS-Friendly: {template_info.get('is_ats_friendly', True)}"
            )
            prompt_parts.append(
                f"Uses Columns: {template_info.get('uses_columns', False)}"
            )

        prompt = "\n".join(prompt_parts)

        result = await Runner.run(
            cv_scoring_agent,
            [{"role": "user", "content": prompt}],
        )

        return result.final_output

    except Exception as e:
        print(f"Error running CV scoring: {e}")
        return None
