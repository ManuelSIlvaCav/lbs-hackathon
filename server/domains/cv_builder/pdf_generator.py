"""
PDF Generator for CV Builder.

Generates ATS-friendly PDF documents from CV data using templates.
"""

from io import BytesIO
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from .models import CVBuilderDocument, CVTemplate


# Font mapping: map common font names to reportlab's built-in fonts
FONT_MAPPING = {
    "Arial": "Helvetica",
    "arial": "Helvetica",
    "Helvetica": "Helvetica",
    "Times New Roman": "Times-Roman",
    "times new roman": "Times-Roman",
    "Times": "Times-Roman",
    "Courier": "Courier",
    "courier": "Courier",
    "Courier New": "Courier",
    "courier new": "Courier",
}


def get_reportlab_font(font_family: str) -> str:
    """Map a font family name to a reportlab-compatible font."""
    return FONT_MAPPING.get(font_family, "Helvetica")


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def create_styles(template: CVTemplate) -> dict:
    """Create paragraph styles based on template settings."""
    styles = getSampleStyleSheet()
    accent_color = colors.Color(*hex_to_rgb(template.accent_color))
    font = get_reportlab_font(template.font_family)

    # Name/Header style
    styles.add(
        ParagraphStyle(
            name="CVName",
            fontName=font,
            fontSize=template.font_size_base + 8,
            leading=(template.font_size_base + 8) * template.line_spacing,
            textColor=accent_color,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )

    # Contact info style
    styles.add(
        ParagraphStyle(
            name="CVContact",
            fontName=font,
            fontSize=template.font_size_base - 1,
            leading=(template.font_size_base - 1) * template.line_spacing,
            alignment=TA_CENTER,
            textColor=colors.gray,
            spaceAfter=12,
        )
    )

    # Section header style
    styles.add(
        ParagraphStyle(
            name="CVSectionHeader",
            fontName=font,
            fontSize=template.font_size_base + 2,
            leading=(template.font_size_base + 2) * template.line_spacing,
            textColor=accent_color,
            spaceBefore=12,
            spaceAfter=6,
            borderWidth=0,
            borderColor=accent_color,
            borderPadding=0,
        )
    )

    # Job title style
    styles.add(
        ParagraphStyle(
            name="CVJobTitle",
            fontName=font,
            fontSize=template.font_size_base + 1,
            leading=(template.font_size_base + 1) * template.line_spacing,
            textColor=colors.black,
            spaceBefore=8,
            spaceAfter=2,
        )
    )

    # Company/Institution style
    styles.add(
        ParagraphStyle(
            name="CVCompany",
            fontName=font,
            fontSize=template.font_size_base,
            leading=template.font_size_base * template.line_spacing,
            textColor=colors.gray,
            spaceAfter=4,
        )
    )

    # Body text style
    styles.add(
        ParagraphStyle(
            name="CVBody",
            fontName=font,
            fontSize=template.font_size_base,
            leading=template.font_size_base * template.line_spacing,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        )
    )

    # Bullet style
    styles.add(
        ParagraphStyle(
            name="CVBullet",
            fontName=font,
            fontSize=template.font_size_base,
            leading=template.font_size_base * template.line_spacing,
            leftIndent=12,
            spaceAfter=2,
        )
    )

    # Skills style
    styles.add(
        ParagraphStyle(
            name="CVSkills",
            fontName=font,
            fontSize=template.font_size_base,
            leading=template.font_size_base * template.line_spacing,
            spaceAfter=4,
        )
    )

    return styles


def generate_cv_pdf(cv: CVBuilderDocument, template: CVTemplate) -> bytes:
    """
    Generate a PDF from CV data using the specified template.

    Args:
        cv: The CV document data
        template: The template to use for styling

    Returns:
        PDF file as bytes
    """
    buffer = BytesIO()

    # Set up document with margins
    margins = template.margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=margins.get("right", 0.5) * inch,
        leftMargin=margins.get("left", 0.5) * inch,
        topMargin=margins.get("top", 0.5) * inch,
        bottomMargin=margins.get("bottom", 0.5) * inch,
    )

    styles = create_styles(template)
    story = []

    # Get section order from template
    section_order = {s.name: (s.order, s.visible) for s in template.sections}

    # =========================================================================
    # Contact Section (always first)
    # =========================================================================
    if section_order.get("contact", (1, True))[1]:
        # Name
        if cv.contact_info.full_name:
            story.append(Paragraph(cv.contact_info.full_name, styles["CVName"]))

        # Contact details line
        contact_parts = []
        if cv.contact_info.email:
            contact_parts.append(cv.contact_info.email)
        if cv.contact_info.phone:
            contact_parts.append(cv.contact_info.phone)
        if cv.contact_info.location:
            contact_parts.append(cv.contact_info.location)
        if cv.contact_info.linkedin:
            # Shorten LinkedIn URL for display
            linkedin = cv.contact_info.linkedin.replace(
                "https://www.linkedin.com/in/", "linkedin.com/in/"
            )
            contact_parts.append(linkedin)

        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), styles["CVContact"]))

        # Separator line
        story.append(Spacer(1, 6))

    # Build sections in order
    sections_to_render = [
        (order, name, visible)
        for name, (order, visible) in section_order.items()
        if name != "contact"  # Contact already rendered
    ]
    sections_to_render.sort(key=lambda x: x[0])

    for _, section_name, visible in sections_to_render:
        if not visible:
            continue

        if section_name == "summary":
            _render_summary(story, cv, styles)
        elif section_name == "experience":
            _render_experience(story, cv, styles)
        elif section_name == "education":
            _render_education(story, cv, styles)
        elif section_name == "skills":
            _render_skills(story, cv, styles)
        elif section_name == "projects":
            _render_projects(story, cv, styles)

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def _render_summary(story: list, cv: CVBuilderDocument, styles: dict):
    """Render professional summary section."""
    if cv.summary and cv.summary.text:
        story.append(Paragraph("PROFESSIONAL SUMMARY", styles["CVSectionHeader"]))
        story.append(Paragraph(cv.summary.text, styles["CVBody"]))
        story.append(Spacer(1, 8))


def _render_experience(story: list, cv: CVBuilderDocument, styles: dict):
    """Render work experience section."""
    if cv.experience:
        story.append(Paragraph("WORK EXPERIENCE", styles["CVSectionHeader"]))

        for exp in cv.experience:
            # Job title
            story.append(Paragraph(f"<b>{exp.role_title}</b>", styles["CVJobTitle"]))

            # Company and dates
            date_str = f"{exp.start_date or ''} - {exp.end_date or 'Present'}"
            company_line = f"{exp.company_name}"
            if exp.location:
                company_line += f" | {exp.location}"
            company_line += f" | {date_str}"
            story.append(Paragraph(company_line, styles["CVCompany"]))

            # Description
            if exp.description:
                story.append(Paragraph(exp.description, styles["CVBody"]))

            # Bullets
            if exp.bullets:
                for bullet in exp.bullets:
                    story.append(Paragraph(f"• {bullet}", styles["CVBullet"]))

            story.append(Spacer(1, 6))


def _render_education(story: list, cv: CVBuilderDocument, styles: dict):
    """Render education section."""
    if cv.education:
        story.append(Paragraph("EDUCATION", styles["CVSectionHeader"]))

        for edu in cv.education:
            # Degree
            degree_parts = []
            if edu.degree_type:
                degree_parts.append(edu.degree_type)
            if edu.degree_name:
                degree_parts.append(edu.degree_name)
            if edu.major:
                degree_parts.append(f"in {edu.major}")

            degree_str = " ".join(degree_parts) if degree_parts else "Degree"
            story.append(Paragraph(f"<b>{degree_str}</b>", styles["CVJobTitle"]))

            # Institution and dates
            date_str = f"{edu.start_date or ''} - {edu.end_date or 'Present'}"
            inst_line = f"{edu.institution} | {date_str}"
            if edu.grades:
                inst_line += f" | {edu.grades}"
            story.append(Paragraph(inst_line, styles["CVCompany"]))

            # Description
            if edu.description:
                story.append(Paragraph(edu.description, styles["CVBody"]))

            # Bullets
            if edu.bullets:
                for bullet in edu.bullets:
                    story.append(Paragraph(f"• {bullet}", styles["CVBullet"]))

            story.append(Spacer(1, 6))


def _render_skills(story: list, cv: CVBuilderDocument, styles: dict):
    """Render skills section."""
    skills = cv.skills
    has_skills = (
        skills.technical_skills
        or skills.soft_skills
        or skills.tools
        or skills.languages
        or skills.certifications
    )

    if has_skills:
        story.append(Paragraph("SKILLS", styles["CVSectionHeader"]))

        if skills.technical_skills:
            story.append(
                Paragraph(
                    f"<b>Technical:</b> {', '.join(skills.technical_skills)}",
                    styles["CVSkills"],
                )
            )

        if skills.tools:
            story.append(
                Paragraph(
                    f"<b>Tools:</b> {', '.join(skills.tools)}",
                    styles["CVSkills"],
                )
            )

        if skills.soft_skills:
            story.append(
                Paragraph(
                    f"<b>Soft Skills:</b> {', '.join(skills.soft_skills)}",
                    styles["CVSkills"],
                )
            )

        if skills.languages:
            story.append(
                Paragraph(
                    f"<b>Languages:</b> {', '.join(skills.languages)}",
                    styles["CVSkills"],
                )
            )

        if skills.certifications:
            story.append(
                Paragraph(
                    f"<b>Certifications:</b> {', '.join(skills.certifications)}",
                    styles["CVSkills"],
                )
            )

        story.append(Spacer(1, 8))


def _render_projects(story: list, cv: CVBuilderDocument, styles: dict):
    """Render projects section."""
    if cv.projects:
        story.append(Paragraph("PROJECTS", styles["CVSectionHeader"]))

        for proj in cv.projects:
            # Project name
            story.append(Paragraph(f"<b>{proj.name}</b>", styles["CVJobTitle"]))

            # Technologies
            if proj.technologies:
                story.append(
                    Paragraph(
                        f"Technologies: {', '.join(proj.technologies)}",
                        styles["CVCompany"],
                    )
                )

            # Description
            if proj.description:
                story.append(Paragraph(proj.description, styles["CVBody"]))

            # Bullets
            if proj.bullets:
                for bullet in proj.bullets:
                    story.append(Paragraph(f"• {bullet}", styles["CVBullet"]))

            story.append(Spacer(1, 6))
