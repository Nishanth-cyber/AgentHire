from agents.common import invoke_structured
from models.schemas import Suggestions
SYSTEM = """You are the Suggestion Agent.
Give actionable resume improvements based only on the supplied analysis into the requested schema.
Return ONLY a valid JSON object.
Do NOT use Markdown code fences (do NOT output ```json ... ```).
Do NOT include explanations outside the JSON object.
Do NOT output <think> tags.
Do NOT add text before or after the JSON.
Do not invent skills, jobs, certifications or achievements.
Return useful, concise recommendations."""
def run(resume, jd, skills, experience, ats): return invoke_structured(SYSTEM, {"resume": resume.model_dump(), "jd": jd.model_dump(), "skills": skills.model_dump(), "experience": experience.model_dump(), "ats": ats.model_dump()}, Suggestions)

