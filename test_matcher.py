import pytest
from app.matcher import analyze_job_match, segment_job_description, calculate_ats_format_score

SAMPLE_JOB_DESC = """
About Us:
We are looking for a Junior Software Engineer to join our core backend team.

Requirements:
- Bachelor's degree in Computer Science or related technical discipline.
- Proficient in Python, SQL, and Git.
- Experience with relational databases like PostgreSQL.
- Understanding of data structures and algorithms.

Preferred Qualifications:
- Experience with Docker and containerization.
- Familiarity with FastAPI or Django.
- Experience with automated testing and CI/CD.
"""

SAMPLE_RESUME_DATA = {
    "contact_info": {
        "name": "Alex Student",
        "email": "alex@university.edu",
        "phone": "555-0199",
        "location": "Boston, MA"
    },
    "summary": "Recent graduate in Computer Science looking to apply skills in Python and SQL.",
    "education": [
        {
            "institution": "Boston University",
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "start_date": "2022",
            "end_date": "2026",
            "gpa": "3.8",
            "highlights": ["Data Structures", "Algorithms"]
        }
    ],
    "experience": [
        {
            "company": "Startup Labs",
            "title": "Software Engineering Intern",
            "bullets": [
                "Built data pipelines using Python and SQL to query PostgreSQL tables.",
                "Automated testing scripts resulting in 20% fewer runtime bugs."
            ]
        }
    ],
    "projects": [
        {
            "name": "Recipe Finder",
            "technologies": ["Python", "PostgreSQL", "Git"],
            "bullets": ["Engineered a searchable database using PostgreSQL and Git version control."]
        }
    ],
    "skills": {
        "technical": ["PostgreSQL", "Data Structures", "Algorithms"],
        "tools_frameworks": ["Git"],
        "languages": ["Python", "SQL"],
        "soft_skills": ["Problem Solving", "Collaboration"]
    },
    "certifications": []
}

def test_segment_job_description():
    req, pref, gen = segment_job_description(SAMPLE_JOB_DESC)
    assert "Requirements:" in SAMPLE_JOB_DESC
    assert "Preferred Qualifications:" in SAMPLE_JOB_DESC
    assert len(req) > 0
    assert len(pref) > 0

def test_analyze_job_match_scoring():
    result = analyze_job_match(SAMPLE_JOB_DESC, SAMPLE_RESUME_DATA)
    assert "overall_score" in result
    assert 10 <= result["overall_score"] <= 99
    assert "score_breakdown" in result
    assert "required_skills" in result["score_breakdown"]
    assert "preferred_skills" in result["score_breakdown"]
    assert "ats_formatting_score" in result["score_breakdown"]

def test_matched_and_missing_terms():
    result = analyze_job_match(SAMPLE_JOB_DESC, SAMPLE_RESUME_DATA)
    matched = [m["term"].lower() for m in result["matched_keywords"]]
    # Python, SQL, PostgreSQL should be matched
    assert any("python" in m for m in matched)
    assert any("sql" in m or "postgresql" in m for m in matched)

    # Missing preferred might include Docker if not in resume
    missing_pref = [m["term"].lower() for m in result["missing_preferred"]]
    assert any("docker" in m for m in missing_pref)

def test_truthfulness_warning_in_suggestions():
    result = analyze_job_match(SAMPLE_JOB_DESC, SAMPLE_RESUME_DATA)
    assert len(result["suggestions"]) > 0
    for s in result["suggestions"]:
        assert "truthfulness_warning" in s
        assert len(s["truthfulness_warning"]) > 10

def test_ats_format_score():
    score, checks = calculate_ats_format_score(SAMPLE_RESUME_DATA, "Sample resume with 300 words and 20% improvements.")
    assert checks["has_contact_info"] is True
    assert checks["has_education"] is True
    assert checks["has_skills_section"] is True
    assert score > 50
