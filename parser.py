import io
import re
import uuid
from typing import Tuple, Dict, Any, List
import pdfplumber

# Common section headers regex
HEADER_PATTERNS = {
    "summary": re.compile(r"^(summary|professional\s+summary|profile|about\s+me|objective)\b", re.IGNORECASE),
    "education": re.compile(r"^(education|academic\s+background|academics|qualifications)\b", re.IGNORECASE),
    "experience": re.compile(r"^(experience|work\s+experience|employment\s+history|professional\s+experience|internships)\b", re.IGNORECASE),
    "projects": re.compile(r"^(projects|personal\s+projects|academic\s+projects|key\s+projects)\b", re.IGNORECASE),
    "skills": re.compile(r"^(skills|technical\s+skills|core\s+competencies|technologies|tools\s+&\s+technologies)\b", re.IGNORECASE),
    "certifications": re.compile(r"^(certifications|licenses|certificates|credentials)\b", re.IGNORECASE),
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
LINKEDIN_REGEX = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", re.IGNORECASE)
GITHUB_REGEX = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)?/?", re.IGNORECASE)
GITHUB_PROFILE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/?", re.IGNORECASE)
GITHUB_REPO_REGEX = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)/?", re.IGNORECASE)

def normalize_url(url: str, default_domain: str = "") -> str:
    if not url:
        return ""
    cleaned = url.strip().rstrip("/")
    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
        if default_domain and not cleaned.startswith(default_domain):
            cleaned = f"{default_domain}/{cleaned.lstrip('/')}"
        cleaned = f"https://{cleaned}"
    return cleaned

KNOWN_TECH_SKILLS = {
    "python", "javascript", "typescript", "c++", "c#", "java", "ruby", "php", "swift", "kotlin", "go", "golang", "rust", "sql", "r", "html", "css",
    "react", "next.js", "nextjs", "vue", "angular", "node.js", "nodejs", "express", "fastapi", "django", "flask", "spring", "spring boot", "asp.net",
    "postgresql", "postgres", "mysql", "mongodb", "sqlite", "redis", "cassandra", "dynamodb", "firebase", "supabase",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "github", "gitlab", "ci/cd", "linux", "rest api", "graphql", "tailwind css", "tailwind", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch"
}

KNOWN_SOFT_SKILLS = {
    "communication", "teamwork", "leadership", "problem solving", "critical thinking", "adaptability", "time management", "collaboration", "agile", "scrum"
}

LOCATION_REGEX = re.compile(r"\b([A-Z][a-zA-Z\s]{2,25},\s*(?:[A-Z]{2}|[A-Z][a-zA-Z\s]{2,20}))\b")

def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, bool, str]:
    """
    Extracts text from PDF bytes using pdfplumber with multiple extraction fallbacks.
    Returns: (extracted_text, is_scanned_warning, warning_message)
    """
    if not file_bytes or len(file_bytes.strip()) == 0:
        return "", True, "The uploaded file is empty (0 bytes)."
    
    if not file_bytes.startswith(b"%PDF"):
        return "", True, "Invalid PDF file: Missing standard %PDF signature."

    extracted_pages = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                return "", True, "The uploaded PDF has no pages."
            
            for page in pdf.pages:
                text = ""
                try:
                    text = page.extract_text(layout=True)
                except Exception:
                    pass
                if not text or not text.strip():
                    try:
                        text = page.extract_text()
                    except Exception:
                        pass
                if not text or not text.strip():
                    try:
                        words = page.extract_words()
                        if words:
                            text = " ".join(w["text"] for w in words if "text" in w)
                    except Exception:
                        pass
                extracted_pages.append(text or "")
    except Exception as e:
        err_str = str(e).lower()
        if "password" in err_str or "encrypt" in err_str:
            return "", True, "The uploaded PDF is password-protected or encrypted. Please remove password protection and try again."
        return "", True, f"Failed to parse PDF: {str(e)}"

    full_text = "\n".join(extracted_pages).strip()
    
    # Check if text is extremely sparse or likely scanned
    alphanumeric_chars = len(re.findall(r"[a-zA-Z0-9]", full_text))
    if alphanumeric_chars < 50:
        warning_msg = (
            "The uploaded PDF appears to be a scanned image or flattened graphic without readable text. "
            "ATS parsers require selectable, machine-readable text. OCR is recommended, or you can paste "
            "or type your resume information directly into the guided builder below."
        )
        return full_text, True, warning_msg

    return full_text, False, ""

def parse_resume_text(raw_text: str) -> Dict[str, Any]:
    """
    Heuristically parses raw text into structured resume sections.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return {
            "contact_info": {},
            "summary": "",
            "education": [],
            "experience": [],
            "projects": [],
            "skills": {"technical": [], "tools_frameworks": [], "soft_skills": [], "languages": []},
            "certifications": []
        }

    # 1. Contact Info heuristics
    contact_info: Dict[str, Any] = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": ""
    }

    # Search for email
    email_match = EMAIL_REGEX.search(raw_text)
    if email_match:
        contact_info["email"] = email_match.group(0)

    # Search for phone
    phone_match = PHONE_REGEX.search(raw_text)
    if phone_match:
        contact_info["phone"] = phone_match.group(0)

    # Search for LinkedIn
    li_match = LINKEDIN_REGEX.search(raw_text)
    if li_match:
        contact_info["linkedin"] = normalize_url(li_match.group(0))

    # Search for GitHub
    gh_match = GITHUB_REGEX.search(raw_text)
    if gh_match:
        contact_info["github"] = normalize_url(gh_match.group(0))

    # Search for location
    loc_match = LOCATION_REGEX.search(raw_text)
    if loc_match:
        contact_info["location"] = loc_match.group(0).strip()

    # Candidate name is often on the first non-empty line
    if lines:
        for possible_name in lines[:4]:
            cleaned_name = re.sub(r"\s+", " ", possible_name).strip()
            # Ignore if looks like header, contact info, URL, or resume label
            if (
                not EMAIL_REGEX.search(cleaned_name)
                and not PHONE_REGEX.search(cleaned_name)
                and not LINKEDIN_REGEX.search(cleaned_name)
                and not GITHUB_REGEX.search(cleaned_name)
                and not any(h in cleaned_name.lower() for h in ["resume", "curriculum", "vitae", "summary", "profile", "contact", "page 1", "page 2"])
                and len(cleaned_name) < 40
                and not cleaned_name.isdigit()
                and any(c.isalpha() for c in cleaned_name)
            ):
                contact_info["name"] = cleaned_name
                break


    # 2. Section segmentation
    sections: Dict[str, List[str]] = {
        "header": [],
        "summary": [],
        "education": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "certifications": []
    }
    current_sec = "header"

    for line in lines:
        matched_section = None
        for sec, pattern in HEADER_PATTERNS.items():
            if pattern.match(line):
                matched_section = sec
                break
        
        if matched_section:
            current_sec = matched_section
        else:
            sections[current_sec].append(line)

    # 3. Parse Summary
    summary_text = " ".join(sections["summary"]) if sections["summary"] else ""

    # 4. Parse Education
    education_entries = []
    if sections["education"]:
        edu_lines = sections["education"]
        current_edu = None
        for line in edu_lines:
            degree_keywords = ["bachelor", "master", "b.s.", "m.s.", "b.tech", "degree", "diploma", "associate", "ph.d."]
            if any(k in line.lower() for k in degree_keywords) or not current_edu:
                if current_edu:
                    education_entries.append(current_edu)
                current_edu = {
                    "id": str(uuid.uuid4()),
                    "institution": line,
                    "degree": "",
                    "field": "",
                    "location": "",
                    "start_date": "",
                    "end_date": "",
                    "gpa": "",
                    "highlights": []
                }
                # Check for degree keywords in line
                for dk in degree_keywords:
                    if dk in line.lower():
                        current_edu["degree"] = line
                        current_edu["institution"] = "University / College"
                        break
            else:
                if "gpa" in line.lower():
                    current_edu["gpa"] = line
                else:
                    current_edu["highlights"].append(line)
        if current_edu:
            education_entries.append(current_edu)

    # 5. Parse Experience
    experience_entries = []
    if sections["experience"]:
        exp_lines = sections["experience"]
        current_exp = None
        for line in exp_lines:
            # Bullet point detection
            if line.startswith(("-", "•", "*", "–")) or (current_exp and len(line) > 30 and not line.isupper()):
                clean_bullet = re.sub(r"^[-•*–\s]+", "", line).strip()
                if current_exp:
                    current_exp["bullets"].append(clean_bullet)
            # Check if line is a date range line for current experience
            date_match = re.search(r"\b(20\d\d|19\d\d|present|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b", line.lower())
            if current_exp and date_match and not current_exp["start_date"] and not line.startswith(("-", "•", "*", "–")):
                current_exp["start_date"] = line
            else:
                if current_exp:
                    experience_entries.append(current_exp)
                current_exp = {
                    "id": str(uuid.uuid4()),
                    "company": line,
                    "title": "Software Engineer / Role",
                    "location": "",
                    "start_date": "",
                    "end_date": "",
                    "is_current": False,
                    "bullets": []
                }
                # If line contains '|' or '-' or ',' might separate title & company
                if " - " in line or " | " in line:
                    parts = line.split(" - ") if " - " in line else line.split(" | ")
                    if len(parts) >= 2:
                        p0, p1 = parts[0].strip(), parts[1].strip()
                        title_cues = ["intern", "engineer", "developer", "analyst", "consultant", "designer", "manager", "lead", "specialist"]
                        if any(cue in p1.lower() for cue in title_cues):
                            current_exp["company"] = p0
                            current_exp["title"] = p1
                        elif any(cue in p0.lower() for cue in title_cues):
                            current_exp["title"] = p0
                            current_exp["company"] = p1
                        else:
                            current_exp["company"] = p0
                            current_exp["title"] = p1
        if current_exp:
            experience_entries.append(current_exp)

    # 6. Parse Projects
    project_entries = []
    if sections["projects"]:
        proj_lines = sections["projects"]
        current_proj = None
        for line in proj_lines:
            # Check for GitHub repository URL or general URL in line
            gh_match = GITHUB_REGEX.search(line)
            extracted_link = ""
            if gh_match:
                extracted_link = normalize_url(gh_match.group(0))
            elif "http://" in line or "https://" in line:
                url_m = re.search(r"https?://[^\s|]+", line)
                if url_m:
                    extracted_link = url_m.group(0)

            if line.startswith(("-", "•", "*", "–")) or (current_proj and len(line) > 30):
                clean_bullet = re.sub(r"^[-•*–\s]+", "", line).strip()
                if current_proj:
                    current_proj["bullets"].append(clean_bullet)
                    if extracted_link and not current_proj.get("link"):
                        current_proj["link"] = extracted_link
            else:
                if current_proj:
                    project_entries.append(current_proj)
                proj_name = line.strip()
                if extracted_link:
                    proj_name = proj_name.replace(extracted_link, "").strip(" -|:\t")
                current_proj = {
                    "id": str(uuid.uuid4()),
                    "name": proj_name or "Project",
                    "role": "Developer / Contributor",
                    "link": extracted_link,
                    "start_date": "",
                    "end_date": "",
                    "technologies": [],
                    "bullets": []
                }
        if current_proj:
            project_entries.append(current_proj)

    # 7. Parse Skills
    skills_data = {
        "technical": [],
        "tools_frameworks": [],
        "soft_skills": [],
        "languages": []
    }
    raw_skills_text = " ".join(sections["skills"]) + " " + raw_text
    raw_lower = raw_skills_text.lower()

    for tech in KNOWN_TECH_SKILLS:
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, raw_lower):
            if tech in ["docker", "kubernetes", "git", "github", "gitlab", "linux", "aws", "gcp", "azure"]:
                skills_data["tools_frameworks"].append(tech.title())
            elif tech in ["python", "javascript", "typescript", "c++", "c#", "java", "go", "ruby", "sql", "r"]:
                skills_data["languages"].append(tech.upper() if tech in ["sql", "r"] else tech.title())
            else:
                skills_data["technical"].append(tech.title())

    for soft in KNOWN_SOFT_SKILLS:
        if soft in raw_lower:
            skills_data["soft_skills"].append(soft.title())

    # Deduplicate
    for k in skills_data:
        skills_data[k] = list(dict.fromkeys(skills_data[k]))

    # 8. Parse Certifications
    cert_entries = []
    if sections["certifications"]:
        for line in sections["certifications"]:
            clean_cert = re.sub(r"^[-•*–\s]+", "", line).strip()
            if clean_cert:
                cert_entries.append({
                    "id": str(uuid.uuid4()),
                    "name": clean_cert,
                    "issuer": "Issuing Org",
                    "date": "",
                    "url": ""
                })

    return {
        "contact_info": contact_info,
        "summary": summary_text,
        "education": education_entries,
        "experience": experience_entries,
        "projects": project_entries,
        "skills": skills_data,
        "certifications": cert_entries
    }
