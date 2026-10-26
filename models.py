import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)


    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    match_reports = relationship("MatchReport", back_populates="user", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="My ATS Resume")
    
    # Structured resume data stored as JSON
    contact_info = Column(JSON, default=dict)
    summary = Column(Text, default="")
    education = Column(JSON, default=list)
    experience = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    skills = Column(JSON, default=dict)
    certifications = Column(JSON, default=list)
    
    # Raw extracted text for review & backup
    raw_text = Column(Text, default="")
    template = Column(String(50), default="classic-ats")
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan", order_by="desc(ResumeVersion.version_num)")
    match_reports = relationship("MatchReport", back_populates="resume", cascade="all, delete-orphan")

class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_num = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    note = Column(String(255), default="Autosave snapshot")
    created_at = Column(DateTime, default=utc_now)

    resume = relationship("Resume", back_populates="versions")

class MatchReport(Base):
    __tablename__ = "match_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    
    job_title = Column(String(255), default="Job Match Target")
    job_company = Column(String(255), default="")
    job_description = Column(Text, nullable=False)
    
    overall_score = Column(Float, nullable=False, default=0.0)
    score_breakdown = Column(JSON, default=dict)
    
    matched_keywords = Column(JSON, default=list)
    missing_required = Column(JSON, default=list)
    missing_preferred = Column(JSON, default=list)
    section_analysis = Column(JSON, default=dict)
    suggestions = Column(JSON, default=list)
    
    truthfulness_note = Column(Text, default="FitCheck strictly advocates truth-in-hiring: only add skills or terms that honestly represent your verified skills and practical experience.")
    created_at = Column(DateTime, default=utc_now)


    user = relationship("User", back_populates="match_reports")
    resume = relationship("Resume", back_populates="match_reports")
