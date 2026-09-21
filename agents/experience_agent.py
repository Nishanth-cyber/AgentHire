from agents.common import invoke_structured
from models.schemas import ExperienceAnalysis
SYSTEM = """You are the Experience and Education Agent.
Compare candidate experience, projects and education with the job requirements into the requested schema.
Return ONLY a valid JSON object.
Do NOT use Markdown code fences (do NOT output ```json ... ```).
Do NOT include explanations, introduction, or reasoning.
Do NOT output <think> tags.
Do NOT add text before or after the JSON.
Do not assign an ATS score. Never invent experience."""
def run(resume, jd): return invoke_structured(SYSTEM, {"resume": resume.model_dump(), "jd": jd.model_dump()}, ExperienceAnalysis)

