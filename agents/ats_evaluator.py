from agents.common import invoke_structured
from models.schemas import ATSAnalysis
SYSTEM = """You are the ATS Evaluator Agent.
Using the resume, job description, skills analysis and experience/education analysis, produce an AI-generated ATS compatibility estimate from 0 to 100 into the requested schema.
Consider skills, requirements, relevant experience, education, projects and keywords.
Return ONLY a valid JSON object.
Do NOT use Markdown code fences (do NOT output ```json ... ```).
Do NOT include explanations outside the JSON object.
Do NOT output <think> tags.
Do NOT add text before or after the JSON.
Do not claim it is an official ATS score."""
def run(resume, jd, skills, experience): return invoke_structured(SYSTEM, {"resume": resume.model_dump(), "jd": jd.model_dump(), "skills": skills.model_dump(), "experience": experience.model_dump()}, ATSAnalysis)

