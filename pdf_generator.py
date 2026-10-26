import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_ats_pdf(resume_data: Dict[str, Any], template: str = "classic-ats") -> bytes:
    """
    Generates a clean, single-column, ATS-optimized selectable text PDF using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,   # 0.5 inch margins
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Define styling and color scheme based on template
    t_key = (template or "modern").lower()
    
    # Defaults: Modern
    primary_color = colors.HexColor("#312e81")   # Indigo-900
    accent_color = colors.HexColor("#4338ca")    # Indigo-700
    line_color = colors.HexColor("#c7d2fe")      # Indigo-200
    body_color = colors.HexColor("#0f172a")      # Slate-900
    heading_font = "Helvetica-Bold"
    body_font = "Helvetica"

    if t_key in ["minimal", "modern-minimal"]:
        primary_color = colors.HexColor("#1e293b")   # Slate-800
        accent_color = colors.HexColor("#64748b")    # Slate-500
        line_color = colors.HexColor("#e2e8f0")      # Slate-200
        body_color = colors.HexColor("#334155")      # Slate-700
        heading_font = "Helvetica-Bold"
        body_font = "Helvetica"
    elif t_key in ["creative"]:
        primary_color = colors.HexColor("#5b21b6")   # Purple-800
        accent_color = colors.HexColor("#7c3aed")    # Violet-600
        line_color = colors.HexColor("#ddd6fe")      # Violet-200
        body_color = colors.HexColor("#1e1b4b")      # Deep violet-slate
        heading_font = "Helvetica-Bold"
        body_font = "Helvetica"
    elif t_key in ["executive"]:
        primary_color = colors.HexColor("#0f172a")   # Deep navy
        accent_color = colors.HexColor("#334155")    # Charcoal
        line_color = colors.HexColor("#94a3b8")      # Slate-400
        body_color = colors.HexColor("#1e293b")      # Slate-800
        heading_font = "Times-Bold"
        body_font = "Times-Roman"
    elif t_key in ["technical", "technical-ats"]:
        primary_color = colors.HexColor("#1e3a8a")   # Blue-900
        accent_color = colors.HexColor("#2563eb")    # Blue-600
        line_color = colors.HexColor("#bfdbfe")      # Blue-200
        body_color = colors.HexColor("#0f172a")      # Slate-900
        heading_font = "Helvetica-Bold"
        body_font = "Helvetica"


    # Custom paragraph styles
    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Normal"],
        fontName=heading_font,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=primary_color
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=accent_color
    )

    section_heading_style = ParagraphStyle(
        "ResumeSectionHeading",
        parent=styles["Normal"],
        fontName=heading_font,
        fontSize=11,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=2,
        textTransform="uppercase"
    )

    subheading_bold = ParagraphStyle(
        "SubHeadingBold",
        parent=styles["Normal"],
        fontName=heading_font,
        fontSize=10,
        leading=13,
        textColor=body_color
    )

    subheading_regular = ParagraphStyle(
        "SubHeadingRegular",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=9,
        leading=12,
        textColor=accent_color
    )

    body_text_style = ParagraphStyle(
        "BodyTextStyle",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=9,
        leading=12.5,
        textColor=body_color
    )

    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=9,
        leading=12.5,
        textColor=body_color,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2
    )


    story = []

    # 1. Contact Information Header
    contact = resume_data.get("contact_info", {})
    name = contact.get("name") or "Your Name"
    story.append(Paragraph(name, name_style))
    story.append(Spacer(1, 3))

    contact_parts = []
    if contact.get("email"):
        contact_parts.append(contact["email"])
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("location"):
        contact_parts.append(contact["location"])
    if contact.get("linkedin"):
        contact_parts.append(contact["linkedin"].replace("https://www.", "").replace("http://www.", ""))
    if contact.get("github"):
        contact_parts.append(contact["github"].replace("https://www.", "").replace("http://www.", ""))
    if contact.get("portfolio"):
        contact_parts.append(contact["portfolio"].replace("https://www.", "").replace("http://www.", ""))

    if contact_parts:
        contact_line = "  •  ".join(contact_parts)
        story.append(Paragraph(contact_line, contact_style))
    
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=line_color, spaceBefore=4, spaceAfter=8))

    def add_section_header(title: str):
        story.append(Paragraph(title, section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=line_color, spaceBefore=2, spaceAfter=6))

    # Helper function to render Education
    def render_education():
        edu_list = resume_data.get("education", [])
        if not edu_list:
            return
        add_section_header("Education")
        for item in edu_list:
            inst = item.get("institution", "")
            deg = item.get("degree", "")
            field = item.get("field", "")
            dates = f"{item.get('start_date', '')} - {item.get('end_date', '')}".strip(" -")
            loc = item.get("location", "")
            gpa = item.get("gpa", "")

            title_row = f"<b>{inst}</b>"
            if loc:
                title_row += f" — <i>{loc}</i>"
            
            degree_row = f"{deg}"
            if field:
                degree_row += f" in {field}"
            if gpa:
                degree_row += f" (GPA: {gpa})"

            # Render two-column header (left: school/degree, right: dates)
            data = [
                [Paragraph(title_row, body_text_style), Paragraph(dates, ParagraphStyle("right", parent=subheading_regular, alignment=TA_RIGHT))],
                [Paragraph(degree_row, subheading_regular), Paragraph("", body_text_style)]
            ]
            t = Table(data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)

            for h in item.get("highlights", []):
                if h:
                    story.append(Paragraph(f"• {h}", bullet_style))
            story.append(Spacer(1, 4))

    # Helper function to render Skills
    def render_skills():
        skills = resume_data.get("skills", {})
        has_skills = any(len(skills.get(k, [])) > 0 for k in ["technical", "tools_frameworks", "languages", "soft_skills"])
        if not has_skills:
            return
        add_section_header("Skills & Competencies")
        if skills.get("technical"):
            story.append(Paragraph(f"<b>Technical Skills:</b> {', '.join(skills['technical'])}", body_text_style))
        if skills.get("tools_frameworks"):
            story.append(Paragraph(f"<b>Tools & Frameworks:</b> {', '.join(skills['tools_frameworks'])}", body_text_style))
        if skills.get("languages"):
            story.append(Paragraph(f"<b>Languages:</b> {', '.join(skills['languages'])}", body_text_style))
        if skills.get("soft_skills"):
            story.append(Paragraph(f"<b>Core Competencies:</b> {', '.join(skills['soft_skills'])}", body_text_style))
        story.append(Spacer(1, 4))

    # Helper function to render Experience
    def render_experience():
        exp_list = resume_data.get("experience", [])
        if not exp_list:
            return
        add_section_header("Professional Experience")
        for item in exp_list:
            comp = item.get("company", "")
            title = item.get("title", "")
            dates = f"{item.get('start_date', '')} - {'Present' if item.get('is_current') else item.get('end_date', '')}".strip(" -")
            loc = item.get("location", "")

            top_left = f"<b>{title}</b> — {comp}"
            if loc:
                top_left += f" ({loc})"

            data = [
                [Paragraph(top_left, body_text_style), Paragraph(dates, ParagraphStyle("right_date", parent=subheading_regular, alignment=TA_RIGHT))]
            ]
            t = Table(data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)

            for b in item.get("bullets", []):
                if b.strip():
                    story.append(Paragraph(f"• {b.strip()}", bullet_style))
            story.append(Spacer(1, 4))

    # Helper function to render Projects
    def render_projects():
        proj_list = resume_data.get("projects", [])
        if not proj_list:
            return
        add_section_header("Projects")
        for item in proj_list:
            p_name = item.get("name", "")
            p_role = item.get("role", "")
            p_tech = ", ".join(item.get("technologies", []))
            dates = f"{item.get('start_date', '')} - {item.get('end_date', '')}".strip(" -")
            p_link = item.get("link", "")

            heading = f"<b>{p_name}</b>"
            if p_role:
                heading += f" | <i>{p_role}</i>"
            if p_tech:
                heading += f" — <font color='#475569'>({p_tech})</font>"

            data = [
                [Paragraph(heading, body_text_style), Paragraph(dates, ParagraphStyle("right_date_p", parent=subheading_regular, alignment=TA_RIGHT))]
            ]
            t = Table(data, colWidths=[420, 120])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)

            if p_link:
                story.append(Paragraph(f"Link: {p_link}", subheading_regular))

            for b in item.get("bullets", []):
                if b.strip():
                    story.append(Paragraph(f"• {b.strip()}", bullet_style))
            story.append(Spacer(1, 4))

    # Helper function to render Certifications
    def render_certifications():
        certs = resume_data.get("certifications", [])
        if not certs:
            return
        add_section_header("Certifications & Licenses")
        for item in certs:
            name = item.get("name", "")
            issuer = item.get("issuer", "")
            date = item.get("date", "")
            line = f"<b>{name}</b>"
            if issuer:
                line += f" — {issuer}"
            if date:
                line += f" ({date})"
            story.append(Paragraph(f"• {line}", bullet_style))
        story.append(Spacer(1, 4))

    # Order sections according to template
    # Summary always near top if present
    summary_text = resume_data.get("summary", "").strip()
    if summary_text:
        add_section_header("Professional Summary")
        story.append(Paragraph(summary_text, body_text_style))
        story.append(Spacer(1, 4))

    if t_key in ["technical", "technical-ats"]:
        # Technical priority: Skills -> Projects -> Experience -> Education -> Certs
        render_skills()
        render_projects()
        render_experience()
        render_education()
        render_certifications()
    elif t_key in ["executive"]:
        # Executive priority: Experience -> Projects -> Education -> Skills -> Certs
        render_experience()
        render_projects()
        render_education()
        render_skills()
        render_certifications()
    else:
        # Modern / Minimal / Creative / Classic ATS: Education -> Experience -> Projects -> Skills -> Certs
        render_education()
        render_experience()
        render_projects()
        render_skills()
        render_certifications()

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
