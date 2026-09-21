import re
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator

def _coerce_string_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        # If it's a comma-separated or newline-separated list in a string
        if "\n" in v:
            return [line.strip().lstrip("•-* ") for line in v.split("\n") if line.strip()]
        if "," in v and len(v.split(",")) > 1:
            return [item.strip() for item in v.split(",") if item.strip()]
        return [v.strip()] if v.strip() else []
    if isinstance(v, dict):
        return [f"{k}: {val}" for k, val in v.items() if val]
    if isinstance(v, list):
        out = []
        for item in v:
            if isinstance(item, str):
                if item.strip():
                    out.append(item.strip())
            elif isinstance(item, dict):
                parts = [f"{k}: {val}" for k, val in item.items() if val]
                if parts:
                    out.append(" - ".join(parts))
            elif item is not None:
                out.append(str(item).strip())
        return out
    return [str(v)]

def _coerce_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if x)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {val}" for k, val in v.items() if val)
    return str(v)

class ResumeData(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def map_synonyms(cls, data: Any):
        if not isinstance(data, dict):
            return data
        d = dict(data)
        # Check candidate / contact sub-dictionary if nested
        for subkey in ["contact", "contact_information", "personal_info", "candidate", "personal_details"]:
            if isinstance(d.get(subkey), dict):
                for k, v in d[subkey].items():
                    if not d.get(k):
                        d[k] = v

        # Map name
        if not d.get("name"):
            for alt in ["full_name", "candidate_name", "applicant_name", "person_name"]:
                if d.get(alt):
                    d["name"] = d[alt]
                    break

        # Map email
        if not d.get("email"):
            for alt in ["email_address", "contact_email", "mail"]:
                if d.get(alt):
                    d["email"] = d[alt]
                    break

        # Map phone
        if not d.get("phone"):
            for alt in ["phone_number", "mobile", "contact_number", "telephone"]:
                if d.get(alt):
                    d["phone"] = d[alt]
                    break

        # Map location
        if not d.get("location"):
            for alt in ["address", "city", "current_location", "residence"]:
                if d.get(alt):
                    d["location"] = d[alt]
                    break

        # Map skills
        if not d.get("skills"):
            for alt in ["technical_skills", "technologies", "hard_skills", "key_skills", "tech_stack", "tools", "competencies"]:
                if d.get(alt):
                    d["skills"] = d[alt]
                    break

        # Map experience
        if not d.get("experience"):
            for alt in ["work_experience", "employment_history", "professional_experience", "work_history", "jobs", "internships"]:
                if d.get(alt):
                    d["experience"] = d[alt]
                    break

        # Map education
        if not d.get("education"):
            for alt in ["academic_background", "qualifications", "education_history", "academics", "degrees"]:
                if d.get(alt):
                    d["education"] = d[alt]
                    break

        # Map projects
        if not d.get("projects"):
            for alt in ["personal_projects", "academic_projects", "key_projects"]:
                if d.get(alt):
                    d["projects"] = d[alt]
                    break

        return d

    @field_validator("skills", "soft_skills", "education", "experience", "projects", "certifications", "achievements", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return _coerce_string_list(v)

    @field_validator("name", "email", "phone", "location", "linkedin", "github", "summary", mode="before")
    @classmethod
    def validate_strs(cls, v):
        return _coerce_str(v)

class JDData(BaseModel):
    job_title: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def map_jd_synonyms(cls, data: Any):
        if not isinstance(data, dict):
            return data
        d = dict(data)
        if not d.get("job_title"):
            for alt in ["title", "role", "position", "designation", "role_title"]:
                if d.get(alt):
                    d["job_title"] = d[alt]
                    break
        if not d.get("required_skills"):
            for alt in ["skills", "technical_skills", "required_qualifications", "must_have_skills", "key_skills", "technologies"]:
                if d.get(alt):
                    d["required_skills"] = d[alt]
                    break

        # If required_skills is still empty, scan responsibilities and text for core technical skills
        if not d.get("required_skills"):
            resps = " ".join(str(x) for x in _coerce_string_list(d.get("responsibilities", [])))
            found_skills = []
            common_skills = [
                "Java", "Spring Boot", "Python", "FastAPI", "Django", "Node.js", "React",
                "SQL", "MySQL", "PostgreSQL", "Docker", "Kubernetes", "AWS", "REST",
                "RESTful APIs", "Git", "Microservices", "C++", "C#", "Go", "TypeScript",
                "JavaScript", "HTML", "CSS", "MongoDB", "Redis", "Linux"
            ]
            for s in common_skills:
                if re.search(r"\b" + re.escape(s) + r"\b", resps, re.IGNORECASE):
                    if s not in found_skills:
                        found_skills.append(s)
            if found_skills:
                d["required_skills"] = found_skills

        return d

    @field_validator("required_skills", "preferred_skills", "experience_requirements", "education_requirements", "responsibilities", "keywords", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return _coerce_string_list(v)

    @field_validator("job_title", mode="before")
    @classmethod
    def validate_title(cls, v):
        return _coerce_str(v)

class SkillsAnalysis(BaseModel):
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    partial_matches: list[str] = Field(default_factory=list)
    skill_analysis: str = ""

    @field_validator("matched_skills", "missing_skills", "partial_matches", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return _coerce_string_list(v)

    @field_validator("skill_analysis", mode="before")
    @classmethod
    def validate_str(cls, v):
        return _coerce_str(v)

class ExperienceAnalysis(BaseModel):
    experience_match: str = ""
    education_match: str = ""
    relevant_experience: list[str] = Field(default_factory=list)
    relevant_projects: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    analysis: str = ""

    @field_validator("relevant_experience", "relevant_projects", "gaps", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return _coerce_string_list(v)

    @field_validator("experience_match", "education_match", "analysis", mode="before")
    @classmethod
    def validate_strs(cls, v):
        return _coerce_str(v)

class ATSAnalysis(BaseModel):
    ats_score: int = 0
    score_explanation: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    keyword_analysis: str = ""
    overall_analysis: str = ""

    @field_validator("ats_score", mode="before")
    @classmethod
    def validate_score(cls, v):
        if isinstance(v, (int, float)):
            return min(100, max(0, int(v)))
        if isinstance(v, str):
            digits = re.findall(r"\d+", v)
            if digits:
                return min(100, max(0, int(digits[0])))
        return 0

    @field_validator("strengths", "weaknesses", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return _coerce_string_list(v)

    @field_validator("score_explanation", "keyword_analysis", "overall_analysis", mode="before")
    @classmethod
    def validate_strs(cls, v):
        return _coerce_str(v)

class Suggestions(BaseModel):
    suggestions: list[str] = Field(default_factory=list)
    keyword_suggestions: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    summary: str = ""

    @field_validator("suggestions", "keyword_suggestions", "missing_skills", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return _coerce_string_list(v)

    @field_validator("summary", mode="before")
    @classmethod
    def validate_str(cls, v):
        return _coerce_str(v)

class AgentEvent(BaseModel):
    sender: str
    receiver: str
    message_type: str
    content: str

class RunResult(BaseModel):
    resume: ResumeData
    jd: JDData
    skills: SkillsAnalysis
    experience: ExperienceAnalysis
    ats: ATSAnalysis
    suggestions: Suggestions
    events: list[AgentEvent] = Field(default_factory=list)
    timings: dict[str, float] = Field(default_factory=dict)
    architecture: str = ""
