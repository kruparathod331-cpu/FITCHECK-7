import pytest
from app.parser import parse_resume_text, extract_text_from_pdf

SAMPLE_RESUME_TEXT = """
Jane Doe
jane.doe@email.com | (555) 123-4567 | San Francisco, CA
linkedin.com/in/janedoe | github.com/janedoe

PROFESSIONAL SUMMARY
Dedicated Computer Science student with a passion for web development, cloud technologies, and database architecture.

EDUCATION
University of California, Berkeley
Bachelor of Science in Computer Science
GPA: 3.85
- Honors: Dean's Honor Roll
- Coursework: Data Structures, Algorithms, Software Engineering

EXPERIENCE
Tech Solutions Inc. - Software Engineering Intern
May 2025 - August 2025
- Developed and maintained full-stack REST API endpoints using FastAPI and PostgreSQL.
- Optimized database queries to improve performance by 30%.
- Collaborated with 5 senior engineers in an agile sprint environment.

PROJECTS
DevBoard - Kanban Task Manager
Lead Developer
- Built a real-time Kanban board using React, TypeScript, and Tailwind CSS.
- Automated deployment with Docker and GitHub Actions.

SKILLS
Technical: Python, JavaScript, TypeScript, SQL, React, FastAPI
Tools & Technologies: Docker, Git, Linux, PostgreSQL
Soft Skills: Teamwork, Problem Solving, Communication
"""

def test_parse_contact_info():
    parsed = parse_resume_text(SAMPLE_RESUME_TEXT)
    contact = parsed["contact_info"]
    assert contact["name"] == "Jane Doe"
    assert "jane.doe@email.com" in contact["email"]
    assert "555" in contact["phone"]
    assert "janedoe" in contact["linkedin"]
    assert "janedoe" in contact["github"]

def test_parse_sections():
    parsed = parse_resume_text(SAMPLE_RESUME_TEXT)
    assert len(parsed["education"]) >= 1
    assert "Berkeley" in parsed["education"][0]["institution"]
    assert len(parsed["experience"]) >= 1
    assert "Tech Solutions" in parsed["experience"][0]["company"] or "Software Engineering" in parsed["experience"][0]["title"]
    assert len(parsed["experience"][0]["bullets"]) >= 1
    assert len(parsed["projects"]) >= 1
    assert "DevBoard" in parsed["projects"][0]["name"]

def test_parse_skills():
    parsed = parse_resume_text(SAMPLE_RESUME_TEXT)
    skills = parsed["skills"]
    assert any("python" in s.lower() for s in skills["languages"] + skills["technical"])
    assert any("docker" in s.lower() for s in skills["tools_frameworks"] + skills["technical"])
    assert any("teamwork" in s.lower() for s in skills["soft_skills"])

def test_empty_or_scanned_pdf_warning():
    # Empty byte test
    text, is_scanned, msg = extract_text_from_pdf(b"")
    assert is_scanned is True
    assert "empty" in msg.lower() or "failed" in msg.lower() or "no pages" in msg.lower()

def test_invalid_header_pdf():
    # Corrupted / invalid header
    text, is_scanned, msg = extract_text_from_pdf(b"This is not a real PDF file header")
    assert is_scanned is True
    assert "invalid" in msg.lower() or "signature" in msg.lower() or "failed" in msg.lower()

def test_generated_pdf_roundtrip():
    from app.pdf_generator import generate_ats_pdf
    pdf_bytes = generate_ats_pdf({
        "contact_info": {"name": "Alex Chen", "email": "alex@example.com", "phone": "555-0199"},
        "summary": "Full Stack Software Engineer",
        "education": [],
        "experience": [],
        "projects": [],
        "skills": {"technical": ["FastAPI", "React"]},
        "certifications": []
    }, template="modern")
    text, is_scanned, msg = extract_text_from_pdf(pdf_bytes)
    assert not is_scanned
    assert "Alex" in text
    assert "FastAPI" in text

