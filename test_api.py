import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_get_sample_resume():
    response = client.get("/api/resumes/sample")
    assert response.status_code == 200
    data = response.json()
    assert "Alex Chen" in data["contact_info"]["name"]
    assert len(data["skills"]["technical"]) > 0

def test_get_sample_jobs():
    response = client.get("/api/matcher/sample-jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert any("Software Engineer" in job["title"] for job in data)

def test_matcher_api_endpoint():
    payload = {
        "job_title": "Junior Developer",
        "job_company": "Acme Corp",
        "job_description": "We need a junior engineer with Python, SQL, and Git experience.",
        "structured_resume": {
            "contact_info": {"name": "Test Candidate", "email": "test@example.com"},
            "skills": {
                "technical": ["SQL"],
                "languages": ["Python", "Git"]
            },
            "experience": [],
            "education": []
        }
    }
    response = client.post("/api/matcher/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "score_breakdown" in data
    assert "matched_keywords" in data
    assert "truthfulness_note" in data

def test_export_pdf_preview():
    payload = {
        "title": "My ATS Resume",
        "contact_info": {
            "name": "Jane Student",
            "email": "jane@example.com",
            "phone": "555-1234"
        },
        "summary": "Quick learner passionate about technology.",
        "education": [],
        "experience": [],
        "projects": [],
        "skills": {
            "technical": ["Python", "FastAPI"],
            "tools_frameworks": ["Git"],
            "soft_skills": ["Teamwork"],
            "languages": ["English"]
        },
        "certifications": [],
        "template": "classic-ats"
    }
    response = client.post("/api/resumes/export-pdf-preview", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # PDF files start with %PDF-
    assert response.content.startswith(b"%PDF-")

def test_auth_registration_and_login():
    import uuid
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": "Test Tester"
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email

    # 2. Duplicate registration should return 400
    dup_res = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_password
    })
    assert dup_res.status_code == 400

    # 3. Successful login
    login_res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Incorrect password should return 401
    bad_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

def test_demo_account():
    response = client.post("/api/auth/demo")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["is_demo"] is True
    assert "demo.student" in data["user"]["email"]

def test_upload_pdf_endpoints():
    from app.pdf_generator import generate_ats_pdf
    pdf_bytes = generate_ats_pdf({
        "contact_info": {"name": "Upload Test Candidate", "email": "upload@test.com"},
        "summary": "Experienced Developer",
        "education": [],
        "experience": [],
        "projects": [],
        "skills": {"technical": ["FastAPI", "React"]},
        "certifications": []
    })

    # Test valid upload
    res = client.post(
        "/api/resumes/upload-pdf",
        files={"file": ("my_resume.pdf", pdf_bytes, "application/pdf")}
    )
    assert res.status_code == 200
    data = res.json()
    assert "raw_text" in data
    assert "char_count" in data
    assert "parsed_sections" in data

    # Test invalid file format
    res_bad_format = client.post(
        "/api/resumes/upload-pdf",
        files={"file": ("resume.txt", b"Plain text resume", "text/plain")}
    )
    assert res_bad_format.status_code == 400

    # Test empty file
    res_empty = client.post(
        "/api/resumes/upload-pdf",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert res_empty.status_code == 400

def test_github_fetch_endpoints():
    # Test repository URL fetch
    res_repo = client.get("/api/resumes/github/fetch?url=https://github.com/torvalds/subsurface")
    assert res_repo.status_code == 200
    repo_data = res_repo.json()
    assert repo_data["type"] == "repository"
    assert repo_data["owner"] == "torvalds"
    assert "project" in repo_data

    # Test profile URL fetch
    res_user = client.get("/api/resumes/github/fetch?url=https://github.com/octocat")
    assert res_user.status_code == 200
    user_data = res_user.json()
    assert user_data["type"] == "profile"
    assert user_data["username"] == "octocat"
    assert "contact_info" in user_data


