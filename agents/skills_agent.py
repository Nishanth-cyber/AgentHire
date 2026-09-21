from agents.common import invoke_structured
from models.schemas import SkillsAnalysis
SYSTEM = """You are the Skills Matching Agent.
Compare resume skills to job requirements semantically. Identify matched, missing and partial skills into the requested schema.
Return ONLY a valid JSON object.
Do NOT use Markdown code fences (do NOT output ```json ... ```).
Do NOT include explanations, introduction, or reasoning.
Do NOT output <think> tags.
Do NOT add text before or after the JSON.
Do not score the whole resume."""
def run(resume, jd): return invoke_structured(SYSTEM, {"resume": resume.model_dump(), "jd": jd.model_dump()}, SkillsAnalysis)

