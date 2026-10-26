import re
import uuid
from typing import Dict, Any, List, Set, Tuple
import spacy

# Load spaCy model with graceful fallback
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = spacy.blank("en")

# Curated Taxonomy of industry keywords & terms
TAXONOMY = {
    "languages": [
        "python", "javascript", "typescript", "c++", "c#", "java", "ruby", "php", "swift", 
        "kotlin", "go", "golang", "rust", "sql", "r", "html", "css", "html5", "css3", "bash", "shell", "dart"
    ],
    "frameworks_and_libraries": [
        "react", "next.js", "nextjs", "vue", "angular", "node.js", "nodejs", "express", "fastapi", 
        "django", "flask", "spring", "spring boot", "asp.net", ".net", "redux", "tailwind css", "tailwind", 
        "bootstrap", "graphql", "rest api", "restful api", "rest", "grpc", "jquery", "pandas", "numpy", 
        "scipy", "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "matplotlib", "seaborn"
    ],
    "databases_and_cloud": [
        "postgresql", "postgres", "mysql", "mongodb", "sqlite", "redis", "cassandra", "dynamodb", 
        "firebase", "supabase", "docker", "kubernetes", "aws", "amazon web services", "azure", 
        "gcp", "google cloud", "git", "github", "gitlab", "ci/cd", "linux", "unix", "kafka", "rabbitmq", 
        "terraform", "ansible", "nginx", "jenkins", "cloudflare", "elasticsearch"
    ],
    "concepts_and_methodologies": [
        "agile", "scrum", "kanban", "test driven development", "tdd", "unit testing", "integration testing", 
        "microservices", "object oriented programming", "oop", "functional programming", "data structures", 
        "algorithms", "system design", "distributed systems", "version control", "code review", "debugging", 
        "performance optimization", "machine learning", "deep learning", "nlp", "computer vision", 
        "data analysis", "etl", "data modeling", "security", "authentication", "authorization", "oauth"
    ],
    "qualifications_and_education": [
        "bachelor", "master", "b.s.", "m.s.", "b.tech", "degree", "computer science", "software engineering", 
        "data science", "information technology", "stem", "internship", "entry level", "junior"
    ],
    "soft_skills": [
        "communication", "teamwork", "leadership", "problem solving", "critical thinking", "adaptability", 
        "time management", "collaboration", "work ethic", "attention to detail", "analytical skills", 
        "presentation", "mentoring", "ownership", "fast learner"
    ]
}

# Invert dictionary for fast lookup: term -> category
TERM_TO_CATEGORY: Dict[str, str] = {}
for cat, terms in TAXONOMY.items():
    for term in terms:
        TERM_TO_CATEGORY[term.lower()] = cat

WEAK_ACTION_VERBS = [
    "responsible for", "helped with", "assisted in", "worked on", "handled", "participated in", "supported"
]
STRONG_ACTION_VERBS = [
    "architected", "engineered", "implemented", "developed", "spearheaded", "optimized", "designed", 
    "automated", "streamlined", "deployed", "scaled", "formulated", "constructed", "orchestrated"
]

def clean_token(text: str) -> str:
    return re.sub(r"[^\w\s\.\#\+\-]", "", text).strip().lower()

def extract_terms_from_text(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts curated and NLP noun chunk terms from given text.
    Returns: { normalized_term: {"raw": term, "category": cat, "count": int} }
    """
    found: Dict[str, Dict[str, Any]] = {}
    text_lower = text.lower()

    # 1. Look for known taxonomy terms (both single and multi-word)
    for term, cat in TERM_TO_CATEGORY.items():
        # Word boundary match
        pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            found[term] = {
                "raw": term,
                "category": cat,
                "count": len(matches)
            }

    # 2. Extract noun chunks and entities via spaCy for role-specific domain terms
    doc = nlp(text[:15000])  # limit length for fast processing
    for chunk in doc.noun_chunks:
        c_text = clean_token(chunk.text)
        if len(c_text) > 2 and len(c_text.split()) <= 3:
            # Filter stop words and numbers
            if c_text not in found and not chunk.root.is_stop and not c_text.isdigit():
                if any(token.pos_ in ["NOUN", "PROPN"] for token in chunk):
                    # Check if it has semantic relevance
                    found[c_text] = {
                        "raw": chunk.text.strip(),
                        "category": "role_terminology",
                        "count": 1
                    }

    return found

def segment_job_description(job_text: str) -> Tuple[str, str, str]:
    """
    Segments job description into:
    - required text
    - preferred text
    - general/overview text
    """
    lines = job_text.splitlines()
    required_lines: List[str] = []
    preferred_lines: List[str] = []
    general_lines: List[str] = []

    current_mode = "general"
    for line in lines:
        lower = line.lower().strip()
        # Check preferred first to prevent 'qualifications' substring collision
        if any(h in lower for h in [
            "preferred qualifications", "preferred:", "nice to have", "bonus points", "bonus qualifications", 
            "desired qualifications", "plus if you have", "what gives you an edge"
        ]):
            current_mode = "preferred"
            continue
        elif any(h in lower for h in [
            "minimum qualifications", "basic qualifications", "required qualifications", 
            "what you need", "what you'll need", "requirements", "must have", "basic requirements", "qualifications:"
        ]):
            current_mode = "required"
            continue
        elif any(h in lower for h in [
            "about us", "about the role", "responsibilities", "what you will do", "benefits", "perks"
        ]):
            current_mode = "general"

        if current_mode == "required":
            required_lines.append(line)
        elif current_mode == "preferred":
            preferred_lines.append(line)
        else:
            general_lines.append(line)

    # If the job description did not have explicit headers, fallback gracefully
    if not required_lines and not preferred_lines:
        return job_text, "", ""
    
    return "\n".join(required_lines), "\n".join(preferred_lines), "\n".join(general_lines)

def search_term_in_resume(term: str, resume_data: Dict[str, Any], raw_text: str) -> List[str]:
    """
    Finds which sections of the resume contain the term.
    """
    sections_found = []
    pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"

    # Check skills section
    skills_obj = resume_data.get("skills", {})
    all_skills_str = " ".join([
        " ".join(skills_obj.get("technical", [])),
        " ".join(skills_obj.get("tools_frameworks", [])),
        " ".join(skills_obj.get("soft_skills", [])),
        " ".join(skills_obj.get("languages", []))
    ]).lower()
    if re.search(pattern, all_skills_str):
        sections_found.append("Skills")

    # Check experience
    exp_text = " ".join([
        f"{e.get('title', '')} {e.get('company', '')} " + " ".join(e.get("bullets", []))
        for e in resume_data.get("experience", [])
    ]).lower()
    if re.search(pattern, exp_text):
        sections_found.append("Experience")

    # Check projects
    proj_text = " ".join([
        f"{p.get('name', '')} {p.get('role', '')} " + " ".join(p.get("technologies", [])) + " " + " ".join(p.get("bullets", []))
        for p in resume_data.get("projects", [])
    ]).lower()
    if re.search(pattern, proj_text):
        sections_found.append("Projects")

    # Check summary
    summary_text = resume_data.get("summary", "").lower()
    if re.search(pattern, summary_text):
        sections_found.append("Summary")

    # Check education
    edu_text = " ".join([
        f"{ed.get('institution', '')} {ed.get('degree', '')} {ed.get('field', '')} " + " ".join(ed.get("highlights", []))
        for ed in resume_data.get("education", [])
    ]).lower()
    if re.search(pattern, edu_text):
        sections_found.append("Education")

    # Check certifications
    cert_text = " ".join([c.get("name", "") for c in resume_data.get("certifications", [])]).lower()
    if re.search(pattern, cert_text):
        sections_found.append("Certifications")

    # Raw text fallback if section data is empty
    if not sections_found and re.search(pattern, raw_text.lower()):
        sections_found.append("Resume Text")

    return sections_found

def calculate_ats_format_score(resume_data: Dict[str, Any], raw_text: str) -> Tuple[float, Dict[str, Any]]:
    """
    Evaluates ATS readability, layout simplicity, and structural completeness.
    """
    checks = {
        "has_contact_info": False,
        "has_education": False,
        "has_experience_or_projects": False,
        "has_skills_section": False,
        "has_quantifiable_metrics": False,
        "clean_text_length": False,
    }

    contact = resume_data.get("contact_info", {})
    if contact.get("name") and (contact.get("email") or contact.get("phone")):
        checks["has_contact_info"] = True

    if resume_data.get("education") or "education" in raw_text.lower():
        checks["has_education"] = True

    if resume_data.get("experience") or resume_data.get("projects") or "experience" in raw_text.lower() or "projects" in raw_text.lower():
        checks["has_experience_or_projects"] = True

    skills = resume_data.get("skills", {})
    if any(len(skills.get(k, [])) > 0 for k in ["technical", "tools_frameworks", "languages", "soft_skills"]) or "skills" in raw_text.lower():
        checks["has_skills_section"] = True

    # Look for numbers/metrics (% or numbers with nouns)
    metrics_matches = re.findall(r"\b(\d+[%kKmM]?|\$\d+|\d+\+?)\b", raw_text)
    if len(metrics_matches) >= 3:
        checks["has_quantifiable_metrics"] = True

    total_words = len(raw_text.split())
    if 150 <= total_words <= 1200:
        checks["clean_text_length"] = True

    passed_count = sum(1 for v in checks.values() if v)
    score = round((passed_count / len(checks)) * 100, 1)
    return score, checks

def analyze_job_match(job_description: str, resume_data: Dict[str, Any], raw_text: str = "") -> Dict[str, Any]:
    """
    Performs comprehensive ATS matching between job description and resume.
    """
    if not raw_text:
        # Build raw text from structured resume if not provided
        parts = []
        c = resume_data.get("contact_info", {})
        parts.append(f"{c.get('name', '')} {c.get('email', '')} {c.get('phone', '')} {c.get('location', '')}")
        parts.append(resume_data.get("summary", ""))
        for ed in resume_data.get("education", []):
            parts.append(f"{ed.get('institution', '')} {ed.get('degree', '')} {ed.get('field', '')} {' '.join(ed.get('highlights', []))}")
        for ex in resume_data.get("experience", []):
            parts.append(f"{ex.get('company', '')} {ex.get('title', '')} {' '.join(ex.get('bullets', []))}")
        for pr in resume_data.get("projects", []):
            parts.append(f"{pr.get('name', '')} {pr.get('role', '')} {' '.join(pr.get('technologies', []))} {' '.join(pr.get('bullets', []))}")
        sk = resume_data.get("skills", {})
        for k in ["technical", "tools_frameworks", "soft_skills", "languages"]:
            parts.append(" ".join(sk.get(k, [])))
        for ct in resume_data.get("certifications", []):
            parts.append(f"{ct.get('name', '')} {ct.get('issuer', '')}")
        raw_text = "\n".join(parts)

    req_text, pref_text, gen_text = segment_job_description(job_description)

    req_terms_dict = extract_terms_from_text(req_text)
    pref_terms_dict = extract_terms_from_text(pref_text)
    gen_terms_dict = extract_terms_from_text(gen_text or job_description)

    # Filter taxonomy/curated terms for required & preferred
    all_matched = []
    missing_required = []
    missing_preferred = []

    # 1. Evaluate Required terms
    req_total = 0
    req_matched = 0
    for term, data in req_terms_dict.items():
        # Prioritize known taxonomy or high-value terms
        if data["category"] in TAXONOMY.keys() or data["count"] > 1:
            req_total += 1
            sections = search_term_in_resume(term, resume_data, raw_text)
            if sections:
                req_matched += 1
                all_matched.append({
                    "term": term.title() if len(term) > 3 else term.upper(),
                    "category": data["category"],
                    "in_resume": True,
                    "frequency_in_job": data["count"],
                    "found_in_sections": sections
                })
            else:
                missing_required.append({
                    "term": term.title() if len(term) > 3 else term.upper(),
                    "category": data["category"],
                    "in_resume": False,
                    "frequency_in_job": data["count"],
                    "found_in_sections": []
                })

    # If no explicit required section was detected, extract top keywords from the entire JD as required
    if req_total == 0:
        for term, data in gen_terms_dict.items():
            if data["category"] in TAXONOMY.keys():
                req_total += 1
                sections = search_term_in_resume(term, resume_data, raw_text)
                if sections:
                    req_matched += 1
                    all_matched.append({
                        "term": term.title() if len(term) > 3 else term.upper(),
                        "category": data["category"],
                        "in_resume": True,
                        "frequency_in_job": data["count"],
                        "found_in_sections": sections
                    })
                else:
                    missing_required.append({
                        "term": term.title() if len(term) > 3 else term.upper(),
                        "category": data["category"],
                        "in_resume": False,
                        "frequency_in_job": data["count"],
                        "found_in_sections": []
                    })

    # 2. Evaluate Preferred terms
    pref_total = 0
    pref_matched = 0
    for term, data in pref_terms_dict.items():
        if data["category"] in TAXONOMY.keys() and term not in req_terms_dict:
            pref_total += 1
            sections = search_term_in_resume(term, resume_data, raw_text)
            if sections:
                pref_matched += 1
                all_matched.append({
                    "term": term.title() if len(term) > 3 else term.upper(),
                    "category": data["category"],
                    "in_resume": True,
                    "frequency_in_job": data["count"],
                    "found_in_sections": sections
                })
            else:
                missing_preferred.append({
                    "term": term.title() if len(term) > 3 else term.upper(),
                    "category": data["category"],
                    "in_resume": False,
                    "frequency_in_job": data["count"],
                    "found_in_sections": []
                })

    # 3. Role terminology overlap (general domain terms)
    domain_total = 0
    domain_matched = 0
    for term, data in gen_terms_dict.items():
        if data["category"] == "role_terminology" and len(term) > 3:
            domain_total += 1
            sections = search_term_in_resume(term, resume_data, raw_text)
            if sections:
                domain_matched += 1

    # 4. Compute Scores
    req_score = round((req_matched / max(req_total, 1)) * 100, 1)
    pref_score = round((pref_matched / max(pref_total, 1)) * 100, 1) if pref_total > 0 else 85.0
    domain_score = round((domain_matched / max(domain_total, 1)) * 100, 1) if domain_total > 0 else 75.0
    ats_fmt_score, ats_checks = calculate_ats_format_score(resume_data, raw_text)

    # Weighted Overall Score
    overall_score = round(
        (0.45 * req_score) + 
        (0.25 * pref_score) + 
        (0.20 * domain_score) + 
        (0.10 * ats_fmt_score), 
        1
    )
    overall_score = min(max(overall_score, 10.0), 99.0)

    # 5. Generate Specific, Truthful Suggestions
    suggestions = []

    # Suggestions for Missing Required Skills
    for item in missing_required[:4]:
        term = item["term"]
        cat = item["category"]
        suggestions.append({
            "id": str(uuid.uuid4()),
            "type": "missing_required",
            "title": f"Address Missing Core Skill: {term}",
            "recommendation": (
                f"The job lists '{term}' ({cat.replace('_', ' ')}). If you have hands-on experience, coursework, "
                f"or personal projects involving {term}, add it to your Skills section and highlight how you applied it."
            ),
            "actionable_example": (
                f"Bullet point example: 'Developed features utilizing {term} to enhance system throughput and reliability.'"
            ),
            "truthfulness_warning": (
                f"Strict Truthfulness Rule: Only list '{term}' if you have genuine familiarity. Never fabricate skills to pass an ATS; "
                f"interviewers will verify technical depth during the hiring rounds."
            )
        })

    # Suggestions for Missing Preferred Skills
    for item in missing_preferred[:2]:
        term = item["term"]
        suggestions.append({
            "id": str(uuid.uuid4()),
            "type": "missing_preferred",
            "title": f"Bonus Qualification Opportunity: {term}",
            "recommendation": (
                f"'{term}' is listed as a preferred or bonus skill. Including it can set your application apart from other early-career candidates."
            ),
            "actionable_example": f"Add '{term}' under your Skills or Projects if you have used it in a team repo or lab.",
            "truthfulness_warning": "Include this only if you can comfortably answer interview questions regarding its concepts and usage."
        })

    # Weak action verb check in resume
    weak_verbs_found = [wv for wv in WEAK_ACTION_VERBS if wv in raw_text.lower()]
    if weak_verbs_found:
        suggestions.append({
            "id": str(uuid.uuid4()),
            "type": "action_verbs",
            "title": "Strengthen Action Verbs",
            "recommendation": f"We detected passive or weak phrasing ({', '.join(weak_verbs_found[:2])}). Replace them with powerful outcome-oriented verbs.",
            "actionable_example": "Instead of 'Responsible for developing the API', use 'Architected and deployed high-performance REST endpoints using FastAPI.'",
            "truthfulness_warning": "Keep verbs accurate to your actual contribution level (e.g. use 'Collaborated with team to implement' vs 'Spearheaded' if you were an apprentice)."
        })

    # Metric quantification check
    if not ats_checks["has_quantifiable_metrics"]:
        suggestions.append({
            "id": str(uuid.uuid4()),
            "type": "quantify",
            "title": "Quantify Impact With Measurable Metrics",
            "recommendation": "Your resume currently contains few quantified accomplishments. Numbers help both ATS heuristics and recruiters evaluate scope.",
            "actionable_example": "Example: 'Reduced page load time by 35% through image optimization and client-side caching' or 'Tested codebase with 40+ unit tests.'",
            "truthfulness_warning": "Use realistic estimates or actual benchmarks from your projects. Never invent fake percentages or revenue figures."
        })

    # ATS Formatting check
    if not ats_checks["clean_text_length"]:
        suggestions.append({
            "id": str(uuid.uuid4()),
            "type": "formatting",
            "title": "Optimize Resume Word Count for Single-Page ATS Readability",
            "recommendation": "Target between 300 and 700 words for an early-career resume. This ensures concise, scannable content that fits standard single-column ATS templates.",
            "actionable_example": "Condense older school projects or trim lengthy summaries down to 2-3 focused sentences.",
            "truthfulness_warning": "Aim for clarity and density rather than filler words."
        })

    score_breakdown = {
        "required_skills": {
            "score": req_score,
            "weight": 0.45,
            "matched_count": req_matched,
            "total_count": req_total,
            "description": "Coverage of essential job requirements, core programming tools, and fundamental qualifications."
        },
        "preferred_skills": {
            "score": pref_score,
            "weight": 0.25,
            "matched_count": pref_matched,
            "total_count": pref_total,
            "description": "Coverage of bonus, desired, or nice-to-have tools that give candidates an edge."
        },
        "role_terminology": {
            "score": domain_score,
            "weight": 0.20,
            "matched_count": domain_matched,
            "total_count": domain_total,
            "description": "Industry domain vocabulary, noun phrases, and role context alignment."
        },
        "ats_formatting_score": {
            "score": ats_fmt_score,
            "weight": 0.10,
            "checks": ats_checks,
            "description": "Clean semantic single-column structure, standard section headers, contact data presence, and readability."
        }
    }

    # Deduplicate all matched list by term
    unique_matched = []
    seen_matched = set()
    for m in all_matched:
        if m["term"].lower() not in seen_matched:
            seen_matched.add(m["term"].lower())
            unique_matched.append(m)

    return {
        "overall_score": overall_score,
        "score_breakdown": score_breakdown,
        "matched_keywords": unique_matched,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
        "section_analysis": {
            "skills_section_coverage": f"{len(resume_data.get('skills', {}).get('technical', []))} technical skills listed",
            "experience_count": len(resume_data.get("experience", [])),
            "projects_count": len(resume_data.get("projects", [])),
            "education_count": len(resume_data.get("education", [])),
            "ats_checks": ats_checks
        },
        "suggestions": suggestions,
        "truthfulness_note": (
            "FitCheck Reminder: This match score is an algorithmic estimate based on keyword coverage and ATS formatting heuristics. "
            "It is NOT an actual ATS guarantee or hiring prediction. Always maintain 100% honesty on your resume — never claim skills "
            "or experience you have not actually performed."
        )
    }
