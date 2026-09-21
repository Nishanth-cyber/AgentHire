from agents.common import invoke_structured
from models.schemas import ResumeData

SYSTEM = """You are the Resume Parser Agent.
Extract all candidate information faithfully from the resume text:
- name: Candidate's full name.
- email: Candidate's email address.
- phone: Candidate's phone number.
- location: Candidate's location or address.
- linkedin: LinkedIn profile link or username if present.
- github: GitHub profile link or username if present.
- summary: Professional summary or objective if present.
- skills: All technical skills, programming languages, frameworks, libraries, tools, and databases.
- soft_skills: Interpersonal or soft skills mentioned.
- education: Degree, field of study, university/college, and year.
- experience: Work history, internships, job roles, company names, durations, and responsibilities.
- projects: Project names, tech stacks used, and descriptions.
- certifications: Certifications, licenses, or courses completed.
- achievements: Honors, awards, or key achievements.
Extract all available details. Do not leave fields blank if present in the text."""

def run(text):
    return invoke_structured(SYSTEM, {"resume_text": text}, ResumeData)
