export interface ContactInfo {
  name: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  github: string;
  portfolio: string;
}

export interface EducationEntry {
  id: string;
  institution: string;
  degree: string;
  field: string;
  location: string;
  start_date: string;
  end_date: string;
  gpa: string;
  highlights: string[];
}

export interface ExperienceEntry {
  id: string;
  company: string;
  title: string;
  location: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  bullets: string[];
}

export interface ProjectEntry {
  id: string;
  name: string;
  role: string;
  link: string;
  start_date: string;
  end_date: string;
  technologies: string[];
  bullets: string[];
}

export interface SkillsData {
  technical: string[];
  tools_frameworks: string[];
  soft_skills: string[];
  languages: string[];
}

export interface CertificationEntry {
  id: string;
  name: string;
  issuer: string;
  date: string;
  url: string;
}

export interface AchievementEntry {
  id: string;
  title: string;
  issuer?: string;
  date?: string;
  description?: string;
}

export interface ResumeData {
  id?: string;
  user_id?: string | null;
  title: string;
  contact_info: ContactInfo;
  summary: string;
  education: EducationEntry[];
  experience: ExperienceEntry[];
  projects: ProjectEntry[];
  skills: SkillsData;
  certifications: CertificationEntry[];
  achievements?: AchievementEntry[];
  raw_text?: string;
  template: string;
  created_at?: string;
  updated_at?: string;
  version_count?: number;
}


export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_num: number;
  snapshot: any;
  note: string;
  created_at: string;
}

export interface KeywordMatchItem {
  term: string;
  category: string;
  in_resume: boolean;
  frequency_in_job: number;
  found_in_sections: string[];
}

export interface SuggestionItem {
  id: string;
  type: string;
  title: string;
  recommendation: string;
  actionable_example: string;
  truthfulness_warning: string;
}

export interface ScoreBreakdownCategory {
  score: number;
  weight: number;
  matched_count?: number;
  total_count?: number;
  checks?: Record<string, boolean>;
  description: string;
}

export interface MatchReportData {
  report_id?: string;
  id?: string;
  job_title: string;
  job_company: string;
  job_description?: string;
  overall_score: number;
  score_breakdown: {
    required_skills: ScoreBreakdownCategory;
    preferred_skills: ScoreBreakdownCategory;
    role_terminology: ScoreBreakdownCategory;
    ats_formatting_score: ScoreBreakdownCategory;
  };
  matched_keywords: KeywordMatchItem[];
  missing_required: KeywordMatchItem[];
  missing_preferred: KeywordMatchItem[];
  section_analysis: {
    skills_section_coverage?: string;
    experience_count?: number;
    projects_count?: number;
    education_count?: number;
    ats_checks?: Record<string, boolean>;
  };
  suggestions: SuggestionItem[];
  truthfulness_note: string;
  created_at?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  is_demo?: boolean;
}

export interface SampleJob {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
}
