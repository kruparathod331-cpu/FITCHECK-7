from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Base Models for Resume Sections ---

class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

class EducationEntry(BaseModel):
    id: str = ""
    institution: str = ""
    degree: str = ""
    field: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    highlights: List[str] = Field(default_factory=list)

class ExperienceEntry(BaseModel):
    id: str = ""
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    bullets: List[str] = Field(default_factory=list)

class ProjectEntry(BaseModel):
    id: str = ""
    name: str = ""
    role: str = ""
    link: str = ""
    start_date: str = ""
    end_date: str = ""
    technologies: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)

class SkillsData(BaseModel):
    technical: List[str] = Field(default_factory=list)
    tools_frameworks: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

class CertificationEntry(BaseModel):
    id: str = ""
    name: str = ""
    issuer: str = ""
    date: str = ""
    url: str = ""

# --- Resume Payloads & Responses ---

class ResumeCreate(BaseModel):
    title: str = "My ATS Resume"
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    skills: SkillsData = Field(default_factory=SkillsData)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    raw_text: str = ""
    template: str = "classic-ats"

class ResumeUpdate(BaseModel):
    title: Optional[str] = None
    contact_info: Optional[ContactInfo] = None
    summary: Optional[str] = None
    education: Optional[List[EducationEntry]] = None
    experience: Optional[List[ExperienceEntry]] = None
    projects: Optional[List[ProjectEntry]] = None
    skills: Optional[SkillsData] = None
    certifications: Optional[List[CertificationEntry]] = None
    raw_text: Optional[str] = None
    template: Optional[str] = None

class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    title: str
    contact_info: Dict[str, Any]
    summary: str
    education: List[Dict[str, Any]]
    experience: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    skills: Dict[str, Any]
    certifications: List[Dict[str, Any]]
    raw_text: str
    template: str
    created_at: datetime
    updated_at: datetime

class ResumeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    template: str
    created_at: datetime
    updated_at: datetime
    version_count: int = 1

class ResumeVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    version_num: int
    snapshot: Dict[str, Any]
    note: str
    created_at: datetime


# --- Extraction Schemas ---

class ParsedSections(BaseModel):
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    skills: SkillsData = Field(default_factory=SkillsData)
    certifications: List[CertificationEntry] = Field(default_factory=list)

class PDFExtractResponse(BaseModel):
    raw_text: str
    char_count: int
    is_scanned_warning: bool
    warning_message: Optional[str] = None
    parsed_sections: ParsedSections

# --- Matching Schemas ---

class MatchRequest(BaseModel):
    job_description: str
    job_title: Optional[str] = "Target Role"
    job_company: Optional[str] = ""
    resume_id: Optional[str] = None
    resume_text: Optional[str] = None
    structured_resume: Optional[Dict[str, Any]] = None

class KeywordMatchItem(BaseModel):
    term: str
    category: str  # "technical", "tool", "soft_skill", "qualification"
    in_resume: bool
    frequency_in_job: int = 1
    found_in_sections: List[str] = Field(default_factory=list)

class SuggestionItem(BaseModel):
    id: str
    type: str  # "missing_required", "missing_preferred", "action_verbs", "quantify", "formatting"
    title: str
    recommendation: str
    actionable_example: str
    truthfulness_warning: str

class ScoreBreakdown(BaseModel):
    required_skills: Dict[str, Any]
    preferred_skills: Dict[str, Any]
    role_terminology: Dict[str, Any]
    ats_formatting_score: Dict[str, Any]

class MatchResponse(BaseModel):
    report_id: Optional[str] = None
    job_title: str
    job_company: str
    overall_score: float
    score_breakdown: ScoreBreakdown
    matched_keywords: List[KeywordMatchItem]
    missing_required: List[KeywordMatchItem]
    missing_preferred: List[KeywordMatchItem]
    section_analysis: Dict[str, Any]
    suggestions: List[SuggestionItem]
    truthfulness_note: str

# --- User & Auth Schemas ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    is_demo: bool = False
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
