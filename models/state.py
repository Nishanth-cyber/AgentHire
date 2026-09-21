from dataclasses import dataclass, field
from models.schemas import ResumeData, JDData, SkillsAnalysis, ExperienceAnalysis, ATSAnalysis, Suggestions, AgentEvent
@dataclass
class Blackboard:
    resume: ResumeData | None = None
    jd: JDData | None = None
    skills: SkillsAnalysis | None = None
    experience: ExperienceAnalysis | None = None
    ats: ATSAnalysis | None = None
    suggestions: Suggestions | None = None
    events: list[AgentEvent] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
